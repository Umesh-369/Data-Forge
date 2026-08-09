from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.db.models import Dataset, DatasetVersion, MLJob
from app.engine.profiler import ProfilerEngine
from app.engine.code_generator import CodeGeneratorEngine
from app.schemas.api import (
    VersionLineageResponse, VersionNode, PreviewDataResponse,
    DatasetChatRequest, DatasetChatResponse, CodeExportResponse, ExcludedOperation
)

from app.services.chat_service import DatasetChatService

router = APIRouter(prefix="/versions", tags=["versions"])

@router.post("/{version_id}/chat", response_model=DatasetChatResponse)
async def chat_with_version_dataset(
    version_id: str,
    body: DatasetChatRequest,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(DatasetVersion).where(DatasetVersion.id == version_id)
    res = await db.execute(stmt)
    version_obj = res.scalars().first()

    if not version_obj:
        raise HTTPException(status_code=404, detail="Dataset version not found.")

    df = ProfilerEngine.load_dataframe(version_obj.file_path)

    answer, computation_trace = await DatasetChatService.process_chat(
        df=df,
        message=body.message,
        conversation_history=body.conversation_history
    )

    return DatasetChatResponse(
        answer=answer,
        computation_trace=computation_trace
    )

@router.get("/{dataset_id}", response_model=VersionLineageResponse)
async def get_version_lineage(
    dataset_id: str,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(DatasetVersion).where(DatasetVersion.dataset_id == dataset_id).order_by(DatasetVersion.version_number.asc())
    res = await db.execute(stmt)
    versions = res.scalars().all()

    if not versions:
        raise HTTPException(status_code=404, detail="No versions found for this dataset.")

    nodes = [
        VersionNode(
            version_id=v.id,
            version_number=v.version_number,
            parent_version_id=v.parent_version_id,
            transformation_op=v.transformation_op,
            row_count=v.row_count,
            col_count=v.col_count,
            created_at=v.created_at
        )
        for v in versions
    ]

    latest_ver = versions[-1]

    return VersionLineageResponse(
        dataset_id=dataset_id,
        current_version_id=latest_ver.id,
        versions=nodes
    )

@router.post("/{dataset_id}/revert/{target_version_id}", response_model=PreviewDataResponse)
async def revert_to_version(
    dataset_id: str,
    target_version_id: str,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(DatasetVersion).where(DatasetVersion.id == target_version_id)
    res = await db.execute(stmt)
    target_version = res.scalars().first()

    if not target_version:
        raise HTTPException(status_code=404, detail="Target version not found.")

    df = ProfilerEngine.load_dataframe(target_version.file_path)

    # Return preview data of target version
    records = df.head(100).replace({float('nan'): None}).to_dict(orient="records")
    return PreviewDataResponse(
        dataset_id=dataset_id,
        version_id=target_version.id,
        version_number=target_version.version_number,
        columns=[str(c) for c in df.columns],
        dtypes={str(c): str(df[c].dtype) for c in df.columns},
        total_rows=len(df),
        rows=records
    )

@router.get("/{version_id}/export/code", response_model=CodeExportResponse)
async def export_version_code(
    version_id: str,
    format: str = Query("py", pattern="^(py|ipynb)$"),
    target_column: Optional[str] = None,
    algorithm: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    # 1. Fetch Target Version
    stmt = select(DatasetVersion).where(DatasetVersion.id == version_id)
    res = await db.execute(stmt)
    version = res.scalars().first()

    if not version:
        raise HTTPException(status_code=404, detail="Dataset version not found.")

    # 2. Fetch Dataset Meta
    ds_stmt = select(Dataset).where(Dataset.id == version.dataset_id)
    ds_res = await db.execute(ds_stmt)
    dataset = ds_res.scalars().first()
    dataset_name = dataset.name if dataset else "dataset"

    # 3. Fetch Lineage up to this version
    lineage_stmt = select(DatasetVersion).where(
        DatasetVersion.dataset_id == version.dataset_id,
        DatasetVersion.version_number <= version.version_number
    ).order_by(DatasetVersion.version_number.asc())
    lineage_res = await db.execute(lineage_stmt)
    all_versions = lineage_res.scalars().all()

    lineage_ops = []
    for ver in all_versions:
        if ver.transformation_op:
            if isinstance(ver.transformation_op, list):
                lineage_ops.extend(ver.transformation_op)
            else:
                lineage_ops.append(ver.transformation_op)

    # 4. Check MLJob if target_column / algorithm not explicitly passed
    final_target = target_column
    final_algo = algorithm
    if not final_target or not final_algo:
        ml_stmt = select(MLJob).where(
            MLJob.dataset_id == version.dataset_id,
            MLJob.status == "completed"
        ).order_by(MLJob.created_at.desc())
        ml_res = await db.execute(ml_stmt)
        latest_ml = ml_res.scalars().first()
        if latest_ml:
            if not final_target:
                final_target = latest_ml.target_column
            if not final_algo and latest_ml.recommendation_json:
                final_algo = latest_ml.recommendation_json.get("algorithm")

    # 5. Generate Standalone Code
    code_str, excluded = CodeGeneratorEngine.generate_code(
        version_number=version.version_number,
        dataset_name=dataset_name,
        lineage_ops=lineage_ops,
        target_column=final_target,
        algorithm=final_algo,
        format_type=format
    )

    ext = "ipynb" if format == "ipynb" else "py"
    filename = f"{dataset_name.lower().replace(' ', '_')}_v{version.version_number}_pipeline.{ext}"

    return CodeExportResponse(
        version_id=version_id,
        format=format,
        filename=filename,
        code=code_str,
        excluded_operations=[ExcludedOperation(**ex) for ex in excluded]
    )


