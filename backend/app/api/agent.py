from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.db.models import DatasetVersion, EditLog
from app.engine.profiler import ProfilerEngine
from app.engine.sandbox import SandboxExecutor, SandboxExecutionError
from app.engine.versioning import VersioningEngine
from app.services.claude_agent import ClaudeAgentService
from app.schemas.api import AgentEditRequest, AgentEditResponse, ConfirmEditRequest, PreviewDataResponse
from app.schemas.tools import OperationPayload

router = APIRouter(prefix="/agent", tags=["agent"])

@router.post("/{dataset_id}/edit", response_model=AgentEditResponse)
async def process_edit_instruction(
    dataset_id: str,
    body: AgentEditRequest,
    version_id: str = None,
    db: AsyncSession = Depends(get_db)
):
    # Fetch current version
    if version_id:
        stmt = select(DatasetVersion).where(DatasetVersion.id == version_id)
    else:
        stmt = select(DatasetVersion).where(DatasetVersion.dataset_id == dataset_id).order_by(DatasetVersion.version_number.desc())

    res = await db.execute(stmt)
    current_version = res.scalars().first()

    if not current_version:
        raise HTTPException(status_code=404, detail="Current dataset version not found.")

    # Load dataframe
    df = ProfilerEngine.load_dataframe(current_version.file_path)

    # 1 & 2. Call Claude Agent Service for structured tool calls
    payload, explanation = await ClaudeAgentService.process_user_instruction(body.user_prompt, df)

    # 3 & 4. Execute in sandbox against COPY to generate diff preview
    try:
        candidate_df, diff_summary = SandboxExecutor.execute_pipeline(df, payload.operations)
    except SandboxExecutionError as e:
        raise HTTPException(status_code=400, detail=f"Operation sandbox execution failed: {str(e)}")

    # 5. Save pending EditLog entry (Invariant I3)
    ops_json_list = [op.model_dump() for op in payload.operations]

    edit_log = EditLog(
        dataset_id=dataset_id,
        version_id=current_version.id,
        user_prompt=body.user_prompt,
        operations_json={"operations": ops_json_list, "explanation": explanation},
        diff_summary_json=diff_summary,
        status="pending"
    )
    db.add(edit_log)
    await db.commit()
    await db.refresh(edit_log)

    return AgentEditResponse(
        edit_log_id=edit_log.id,
        user_prompt=body.user_prompt,
        proposed_operations=ops_json_list,
        explanation=explanation,
        diff_summary=diff_summary
    )

@router.post("/{dataset_id}/confirm", response_model=PreviewDataResponse)
async def confirm_or_reject_edit(
    dataset_id: str,
    body: ConfirmEditRequest,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(EditLog).where(EditLog.id == body.edit_log_id)
    res = await db.execute(stmt)
    edit_log = res.scalars().first()

    if not edit_log:
        raise HTTPException(status_code=404, detail="Edit log request not found.")

    if edit_log.status != "pending":
        raise HTTPException(status_code=400, detail=f"Edit log is already {edit_log.status}.")

    if body.action == "reject":
        edit_log.status = "rejected"
        await db.commit()
        # Return current unmutated dataset state
        ver_stmt = select(DatasetVersion).where(DatasetVersion.id == edit_log.version_id)
        ver_res = await db.execute(ver_stmt)
        curr_ver = ver_res.scalars().first()
        df = ProfilerEngine.load_dataframe(curr_ver.file_path)
        records = df.head(100).replace({float('nan'): None}).to_dict(orient="records")
        return PreviewDataResponse(
            dataset_id=dataset_id,
            version_id=curr_ver.id,
            version_number=curr_ver.version_number,
            columns=[str(c) for c in df.columns],
            dtypes={str(c): str(df[c].dtype) for c in df.columns},
            total_rows=len(df),
            rows=records
        )

    # Action is CONFIRM: apply operations to create new version snapshot
    ver_stmt = select(DatasetVersion).where(DatasetVersion.id == edit_log.version_id)
    ver_res = await db.execute(ver_stmt)
    parent_version = ver_res.scalars().first()

    df = ProfilerEngine.load_dataframe(parent_version.file_path)

    # Re-parse operations payload
    ops_data = edit_log.operations_json.get("operations", [])
    payload = OperationPayload(operations=ops_data)

    new_df, _ = SandboxExecutor.execute_pipeline(df, payload.operations)
    new_profile = ProfilerEngine.profile(new_df)

    # Create new immutable dataset version (Invariants I1, I2)
    new_version = await VersioningEngine.create_new_version(
        db=db,
        dataset_id=dataset_id,
        df=new_df,
        parent_version_id=parent_version.id,
        transformation_op=edit_log.operations_json,
        profile_json=new_profile
    )

    edit_log.status = "applied"
    await db.commit()

    records = new_df.head(100).replace({float('nan'): None}).to_dict(orient="records")
    return PreviewDataResponse(
        dataset_id=dataset_id,
        version_id=new_version.id,
        version_number=new_version.version_number,
        columns=[str(c) for c in new_df.columns],
        dtypes={str(c): str(new_df[c].dtype) for c in new_df.columns},
        total_rows=len(new_df),
        rows=records
    )
