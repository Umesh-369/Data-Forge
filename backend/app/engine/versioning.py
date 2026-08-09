import os
import shutil
import pandas as pd
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import DatasetVersion
from app.core.config import settings

class VersioningEngine:
    @staticmethod
    async def create_new_version(
        db: AsyncSession,
        dataset_id: str,
        df: pd.DataFrame,
        parent_version_id: str,
        transformation_op: Dict[str, Any],
        profile_json: Dict[str, Any]
    ) -> DatasetVersion:
        # Determine next version number
        stmt = select(DatasetVersion).where(DatasetVersion.dataset_id == dataset_id)
        res = await db.execute(stmt)
        all_versions = res.scalars().all()
        next_ver_num = len(all_versions) + 1

        # Save snapshot file to data_scratch
        filename = f"{dataset_id}_v{next_ver_num}.csv"
        file_path = os.path.join(settings.STORAGE_DIR, filename)
        df.to_csv(file_path, index=False)

        new_version = DatasetVersion(
            dataset_id=dataset_id,
            version_number=next_ver_num,
            parent_version_id=parent_version_id,
            file_path=file_path,
            row_count=len(df),
            col_count=len(df.columns),
            transformation_op=transformation_op,
            profile_json=profile_json
        )
        db.add(new_version)
        await db.commit()
        await db.refresh(new_version)
        return new_version

    @staticmethod
    async def get_lineage_tree(db: AsyncSession, dataset_id: str) -> List[DatasetVersion]:
        stmt = select(DatasetVersion).where(DatasetVersion.dataset_id == dataset_id).order_by(DatasetVersion.version_number.asc())
        res = await db.execute(stmt)
        return res.scalars().all()
