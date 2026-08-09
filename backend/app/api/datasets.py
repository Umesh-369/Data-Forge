import os
import shutil
import pandas as pd
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.config import settings
from app.db.models import Dataset, DatasetVersion
from app.engine.profiler import ProfilerEngine
from app.schemas.api import DatasetSummaryResponse, ProfileResponse, PreviewDataResponse

router = APIRouter(prefix="/datasets", tags=["datasets"])

@router.get("", response_model=List[DatasetSummaryResponse])
async def list_datasets(db: AsyncSession = Depends(get_db)):
    stmt = select(Dataset).order_by(Dataset.created_at.desc())
    res = await db.execute(stmt)
    datasets = res.scalars().all()

    result = []
    for d in datasets:
        # Get latest version
        ver_stmt = select(DatasetVersion).where(DatasetVersion.dataset_id == d.id).order_by(DatasetVersion.version_number.desc())
        ver_res = await db.execute(ver_stmt)
        latest_ver = ver_res.scalars().first()

        if latest_ver:
            result.append(DatasetSummaryResponse(
                id=d.id,
                name=d.name,
                original_filename=d.original_filename,
                file_type=d.file_type,
                current_version_id=latest_ver.id,
                version_number=latest_ver.version_number,
                row_count=latest_ver.row_count,
                col_count=latest_ver.col_count,
                created_at=d.created_at
            ))
    return result

@router.post("/upload", response_model=DatasetSummaryResponse)
async def upload_dataset(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    filename = file.filename or "uploaded_file.csv"
    ext = os.path.splitext(filename)[1].lower()

    if ext not in [".csv", ".xlsx", ".xls", ".json", ".parquet"]:
        raise HTTPException(status_code=400, detail="Unsupported file format. Accepted formats: CSV, XLSX, JSON, Parquet.")

    dataset = Dataset(
        name=os.path.splitext(filename)[0].replace("_", " ").title(),
        original_filename=filename,
        file_type=ext.replace(".", "")
    )
    db.add(dataset)
    await db.commit()
    await db.refresh(dataset)

    # Save original file snapshot (Invariant I1)
    save_path = os.path.join(settings.STORAGE_DIR, f"{dataset.id}_v1{ext}")
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    df = ProfilerEngine.load_dataframe(save_path)
    profile_data = ProfilerEngine.profile(df)

    version = DatasetVersion(
        dataset_id=dataset.id,
        version_number=1,
        parent_version_id=None,
        file_path=save_path,
        row_count=len(df),
        col_count=len(df.columns),
        transformation_op={"type": "initial_upload", "filename": filename},
        profile_json=profile_data
    )
    db.add(version)
    await db.commit()
    await db.refresh(version)

    return DatasetSummaryResponse(
        id=dataset.id,
        name=dataset.name,
        original_filename=dataset.original_filename,
        file_type=dataset.file_type,
        current_version_id=version.id,
        version_number=version.version_number,
        row_count=version.row_count,
        col_count=version.col_count,
        created_at=dataset.created_at
    )

@router.post("/load-seed/{seed_name}", response_model=DatasetSummaryResponse)
async def load_seed_dataset(
    seed_name: str,
    db: AsyncSession = Depends(get_db)
):
    seed_filename = "sample_students.csv" if "student" in seed_name.lower() else "salary_data.csv"
    seed_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "seed_data", seed_filename)

    if not os.path.exists(seed_path):
        raise HTTPException(status_code=404, detail="Seed dataset not found.")

    dataset = Dataset(
        name="Sample Students" if "student" in seed_filename else "Employee Salaries",
        original_filename=seed_filename,
        file_type="csv"
    )
    db.add(dataset)
    await db.commit()
    await db.refresh(dataset)

    save_path = os.path.join(settings.STORAGE_DIR, f"{dataset.id}_v1.csv")
    shutil.copyfile(seed_path, save_path)

    df = ProfilerEngine.load_dataframe(save_path)
    profile_data = ProfilerEngine.profile(df)

    version = DatasetVersion(
        dataset_id=dataset.id,
        version_number=1,
        parent_version_id=None,
        file_path=save_path,
        row_count=len(df),
        col_count=len(df.columns),
        transformation_op={"type": "seed_dataset", "filename": seed_filename},
        profile_json=profile_data
    )
    db.add(version)
    await db.commit()
    await db.refresh(version)

    return DatasetSummaryResponse(
        id=dataset.id,
        name=dataset.name,
        original_filename=dataset.original_filename,
        file_type=dataset.file_type,
        current_version_id=version.id,
        version_number=version.version_number,
        row_count=version.row_count,
        col_count=version.col_count,
        created_at=dataset.created_at
    )

@router.get("/{dataset_id}/profile", response_model=ProfileResponse)
async def get_dataset_profile(
    dataset_id: str,
    version_id: str = None,
    db: AsyncSession = Depends(get_db)
):
    if version_id and version_id.strip() and version_id.lower() not in ("undefined", "null", "none"):
        stmt = select(DatasetVersion).where(DatasetVersion.id == version_id)
    else:
        stmt = select(DatasetVersion).where(DatasetVersion.dataset_id == dataset_id).order_by(DatasetVersion.version_number.desc())

    res = await db.execute(stmt)
    version = res.scalars().first()

    if not version:
        raise HTTPException(status_code=404, detail="Dataset version not found.")

    if not version.profile_json:
        df = ProfilerEngine.load_dataframe(version.file_path)
        version.profile_json = ProfilerEngine.profile(df)
        await db.commit()

    pj = version.profile_json
    return ProfileResponse(
        dataset_id=dataset_id,
        version_id=version.id,
        version_number=version.version_number,
        row_count=pj["row_count"],
        col_count=pj["col_count"],
        duplicate_rows=pj["duplicate_rows"],
        total_missing_cells=pj["total_missing_cells"],
        columns=pj["columns"]
    )

@router.get("/{dataset_id}/preview", response_model=PreviewDataResponse)
async def preview_dataset(
    dataset_id: str,
    version_id: str = None,
    limit: int = Query(100, ge=1, le=10000),
    db: AsyncSession = Depends(get_db)
):
    if version_id and version_id.strip() and version_id.lower() not in ("undefined", "null", "none"):
        stmt = select(DatasetVersion).where(DatasetVersion.id == version_id)
    else:
        stmt = select(DatasetVersion).where(DatasetVersion.dataset_id == dataset_id).order_by(DatasetVersion.version_number.desc())

    res = await db.execute(stmt)
    version = res.scalars().first()

    if not version:
        raise HTTPException(status_code=404, detail="Dataset version not found.")

    df = ProfilerEngine.load_dataframe(version.file_path)
    preview_df = df.head(limit).copy()
    preview_df = preview_df.replace({pd.NA: None, float('nan'): None})

    records = preview_df.to_dict(orient="records")
    dtypes = {str(c): str(df[c].dtype) for c in df.columns}

    return PreviewDataResponse(
        dataset_id=dataset_id,
        version_id=version.id,
        version_number=version.version_number,
        columns=[str(c) for c in df.columns],
        dtypes=dtypes,
        total_rows=len(df),
        rows=records
    )

@router.get("/{dataset_id}/export")
async def export_dataset(
    dataset_id: str,
    version_id: str = None,
    format: str = Query("csv", pattern="^(csv|json|xlsx)$"),
    db: AsyncSession = Depends(get_db)
):
    if version_id and version_id.strip() and version_id.lower() not in ("undefined", "null", "none"):
        stmt = select(DatasetVersion).where(DatasetVersion.id == version_id)
    else:
        stmt = select(DatasetVersion).where(DatasetVersion.dataset_id == dataset_id).order_by(DatasetVersion.version_number.desc())

    res = await db.execute(stmt)
    version = res.scalars().first()

    if not version:
        raise HTTPException(status_code=404, detail="Dataset version not found.")

    ds_stmt = select(Dataset).where(Dataset.id == dataset_id)
    ds_res = await db.execute(ds_stmt)
    dataset = ds_res.scalars().first()
    dataset_name = dataset.name if dataset else "dataset"
    safe_name = dataset_name.lower().replace(" ", "_").replace("/", "_")

    df = ProfilerEngine.load_dataframe(version.file_path)

    if format == "csv":
        csv_data = df.to_csv(index=False)
        filename = f"{safe_name}_v{version.version_number}.csv"
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    elif format == "json":
        json_data = df.to_json(orient="records", indent=2)
        filename = f"{safe_name}_v{version.version_number}.json"
        return Response(
            content=json_data,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    elif format == "xlsx":
        import io
        output = io.BytesIO()
        try:
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)
        except Exception:
            # Fallback if openpyxl is not installed or errors out
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)
        output.seek(0)
        filename = f"{safe_name}_v{version.version_number}.xlsx"
        return Response(
            content=output.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )

