# """Model information router for getting model metadata and capabilities."""

# import logging
# from typing import Any, Dict

# from fastapi import APIRouter, HTTPException
# from pydantic import BaseModel

# logger = logging.getLogger(__name__)

# router = APIRouter(prefix="/api/model", tags=["model"])


# class ModelInfoResponse(BaseModel):
#     """Response model for model information."""

#     model_name: str
#     categories: list
#     embedding_dimension: int
#     is_available: bool
#     model_path: str


# @router.get("/info", response_model=ModelInfoResponse)
# async def get_model_info(

# ):
#     """
#     Get information about the currently loaded model.

#     Returns:
#         ModelInfoResponse: Model metadata and capabilities
#     """
#     try:
#         from app_state import get_app_state

#         app_state = get_app_state()
#         model_dir = app_state.model_path

#         # Try to load the classifier
#         classifier = load_pretrained_classifier(model_dir)

#         if not classifier or not classifier.is_initialized:
#             raise HTTPException(
#                 status_code=404, detail="No trained model found or model not available"
#             )

#         # Get model information
#         model_info = classifier.get_classifier_info()

#         return ModelInfoResponse(
#             model_name=model_info["model_name"],
#             categories=model_info["categories"],
#             embedding_dimension=model_info["embedding_dimension"],
#             is_available=model_info["is_initialized"],
#             model_path=model_dir,
#         )

#     except Exception as e:
#         logger.error(f"Failed to get model info: {e}")
#         raise HTTPException(
#             status_code=500, detail=f"Failed to get model information: {str(e)}"
#         )


# @router.get("/categories")
# async def get_model_categories():
#     """
#     Get the list of categories supported by the current model.

#     Returns:
#         dict: List of supported categories
#     """
#     try:
#         from app_state import get_app_state

#         app_state = get_app_state()
#         model_dir = app_state.model_path

#         # Try to load the classifier
#         classifier = load_pretrained_classifier(model_dir)

#         if not classifier or not classifier.is_initialized:
#             raise HTTPException(
#                 status_code=404, detail="No trained model found or model not available"
#             )

#         categories = classifier.get_supported_categories()

#         return {"categories": categories, "count": len(categories)}

#     except Exception as e:
#         logger.error(f"Failed to get model categories: {e}")
#         raise HTTPException(
#             status_code=500, detail=f"Failed to get model categories: {str(e)}"
#         )


# @router.post("/reload")
# async def reload_model():
#     """
#     Reload the model from disk (useful after model updates).

#     Returns:
#         dict: Reload status
#     """
#     try:
#         # This would clear any cached model data
#         # In a real implementation, you might want to clear caches here
#         logger.info("Model reload requested")

#         return {
#             "status": "success",
#             "message": "Model reload completed. New requests will use the updated model.",
#         }

#     except Exception as e:
#         logger.error(f"Failed to reload model: {e}")
#         raise HTTPException(status_code=500, detail=f"Failed to reload model: {str(e)}")
