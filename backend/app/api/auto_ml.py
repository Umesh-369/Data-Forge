from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.db.models import Dataset, DatasetVersion, MLJob
from app.engine.profiler import ProfilerEngine
from app.engine.auto_ml import AutoMLEngine
from app.schemas.api import AutoMLRequest, AutoMLRecommendResponse, TrainModelRequest, TrainModelResponse, AutoPipelineResponse

router = APIRouter(prefix="/auto-ml", tags=["auto-ml"])

@router.post("/{dataset_id}/auto-pipeline", response_model=AutoPipelineResponse)
async def auto_pipeline(
    dataset_id: str,
    body: AutoMLRequest = AutoMLRequest(),
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

    df = ProfilerEngine.load_dataframe(version.file_path)

    try:
        pipeline_res = AutoMLEngine.run_auto_pipeline(df, body.target_column)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"AutoML pipeline failed: {str(e)}")

    train_res = pipeline_res["training_results"]

    ml_job = MLJob(
        dataset_id=dataset_id,
        version_id=version.id,
        target_column=pipeline_res["target_column"],
        problem_type=pipeline_res["problem_type"],
        recommendation_json={
            "algorithm": pipeline_res["selected_algorithm"],
            "candidates": pipeline_res["candidates"],
            "cleaning_logs": pipeline_res["cleaning_logs"],
            "lineage_ops": pipeline_res["lineage_ops"],
            "target_detection_reason": pipeline_res["target_detection_reason"]
        },
        model_results_json=train_res,
        status="completed"
    )
    db.add(ml_job)
    await db.commit()
    await db.refresh(ml_job)

    train_model_resp = TrainModelResponse(
        job_id=ml_job.id,
        status="completed",
        problem_type=train_res["problem_type"],
        metrics=train_res["metrics"],
        confusion_matrix=train_res.get("confusion_matrix"),
        feature_importances=train_res.get("feature_importances"),
        residual_plot_data=train_res.get("residual_plot_data")
    )

    return AutoPipelineResponse(
        dataset_id=dataset_id,
        version_id=version.id,
        target_column=pipeline_res["target_column"],
        target_detection_reason=pipeline_res["target_detection_reason"],
        cleaning_logs=pipeline_res["cleaning_logs"],
        problem_type=pipeline_res["problem_type"],
        class_balance=pipeline_res["class_balance"],
        feature_count=pipeline_res["feature_count"],
        candidates=pipeline_res["candidates"],
        selected_algorithm=pipeline_res["selected_algorithm"],
        training_results=train_model_resp,
        cleaned_row_count=pipeline_res["cleaned_row_count"],
        cleaned_col_count=pipeline_res["cleaned_col_count"]
    )

@router.get("/{dataset_id}/export-cleaned")
async def export_cleaned_dataset(
    dataset_id: str,
    target_column: str = None,
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

    # Detect target if not passed
    if not target_column:
        target_column, _ = AutoMLEngine.auto_detect_target(df)

    # Perform auto-cleaning
    df_cleaned, _, _ = AutoMLEngine.auto_clean_and_preprocess(df, target_column)

    if format == "csv":
        csv_data = df_cleaned.to_csv(index=False)
        filename = f"{safe_name}_cleaned_v{version.version_number}.csv"
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    elif format == "json":
        json_data = df_cleaned.to_json(orient="records", indent=2)
        filename = f"{safe_name}_cleaned_v{version.version_number}.json"
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
                df_cleaned.to_excel(writer, index=False)
        except Exception:
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_cleaned.to_excel(writer, index=False)
        output.seek(0)
        filename = f"{safe_name}_cleaned_v{version.version_number}.xlsx"
        return Response(
            content=output.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )

@router.post("/{dataset_id}/recommend", response_model=AutoMLRecommendResponse)
async def recommend_algorithms(
    dataset_id: str,
    body: AutoMLRequest,
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

    df = ProfilerEngine.load_dataframe(version.file_path)
    target_col = body.target_column
    if not target_col:
        target_col, _ = AutoMLEngine.auto_detect_target(df)

    try:
        rec_data = AutoMLEngine.analyze_dataset_and_recommend(df, target_col)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return AutoMLRecommendResponse(
        dataset_id=dataset_id,
        version_id=version.id,
        target_column=rec_data["target_column"],
        problem_type=rec_data["problem_type"],
        class_balance=rec_data["class_balance"],
        feature_count=rec_data["feature_count"],
        candidates=rec_data["candidates"]
    )

@router.post("/{dataset_id}/train", response_model=TrainModelResponse)
async def train_model(
    dataset_id: str,
    body: TrainModelRequest,
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

    df = ProfilerEngine.load_dataframe(version.file_path)

    try:
        train_results = AutoMLEngine.train_model(df, body.target_column, body.selected_algorithm)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Model training failed: {str(e)}")

    ml_job = MLJob(
        dataset_id=dataset_id,
        version_id=version.id,
        target_column=body.target_column,
        problem_type=train_results["problem_type"],
        recommendation_json={"algorithm": body.selected_algorithm},
        model_results_json=train_results,
        status="completed"
    )
    db.add(ml_job)
    await db.commit()
    await db.refresh(ml_job)

    return TrainModelResponse(
        job_id=ml_job.id,
        status="completed",
        problem_type=train_results["problem_type"],
        metrics=train_results["metrics"],
        confusion_matrix=train_results.get("confusion_matrix"),
        feature_importances=train_results.get("feature_importances"),
        residual_plot_data=train_results.get("residual_plot_data")
    )

