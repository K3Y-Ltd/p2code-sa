import logging

from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.session import Session

from .models import InferenceResult, StatusEnum


logger = logging.getLogger("inference_pipeline.api.app")


class InferenceRepository:
    """
    This class allows interaction with the InferenceResult table.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, id: int) -> InferenceResult:
        """
        Get an inference result by its ID.

        Parameters
        ----------
        id : int
            The ID of the inference result.

        Returns
        -------
        InferenceResult
            The inference result with the given ID.
        """

        return (
            self.session.query(InferenceResult).filter(InferenceResult.id == id).first()
        )

    def get_by_sa_hash(self, sa_hash: str) -> InferenceResult:
        """
        Get an inference result by its SA hash.

        Parameters
        ----------
        sa_hash : str
            The SA hash of the inference result.

        Returns
        -------
        InferenceResult
            The inference result with the given SA hash.
        """
        return (
            self.session.query(InferenceResult)
            .filter(InferenceResult.sa_hash == sa_hash)
            .first()
        )

    def get_stix_report_by_sa_hash(self, sa_hash: str) -> dict:
        """
        Get STIX report by SA hash.

        Parameters
        ----------
        sa_hash : str
            The SA hash of the inference result.

        Returns
        -------
        Dict | None
            The STIX report with the given SA hash if it exists, else None.
        """

        result = (
            self.session.query(InferenceResult)
            .filter(InferenceResult.sa_hash == sa_hash)
            .first()
        )
        return result.stix_report if result else None

    def get_all(self) -> list[InferenceResult]:
        """
        Get all inference results.

        Returns
        -------
        List[InferenceResult]
            All inference results.
        """
        return self.session.query(InferenceResult).all()

    def create_record(
        self, sa_hash: str, stix_report: dict, application_area: int
    ) -> InferenceResult:
        """
        Create a new inference result record.

        Parameters
        ----------
        sa_hash : str
            The SA hash of the inference result
        stix_report : Dict
            The STIX report.
        application_area : int
            The application area identifier. A number between 1-4.

        Returns
        -------
        InferenceResult
            The new inference result record.
        """

        # Check if the same SA hash already exists
        existing_result = self.get_by_sa_hash(sa_hash)
        if existing_result:
            return existing_result

        try:
            result = InferenceResult(
                sa_hash=sa_hash,
                stix_report=stix_report,
                created_at=datetime.now(),
                application_area=application_area,
                status=StatusEnum.COMPLETED,
            )
            self.session.add(result)
            self.session.commit()
            return result
        except Exception as e:
            self.session.rollback()
            raise e

    # def delete_record_by_id(self, id: int) -> bool:
    #     """
    #     Delete an inference result record.

    #     Args:
    #         id: The ID of the inference result

    #     Returns:
    #         True if the record was deleted, False otherwise
    #     """
    #     try:

    #         deleted = (
    #             self.session.query(InferenceResult)
    #             .filter(InferenceResult.id == id)
    #             .delete()
    #         )
    #         self.session.commit()
    #         return deleted > 0
    #     except SQLAlchemyError as e:
    #         self.session.rollback()
    #         raise e
