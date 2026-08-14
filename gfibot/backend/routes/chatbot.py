import logging
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from mongoengine.queryset.visitor import Q

from gfibot.collections import ChatbotSession, ChatMessage, GfiQueries, Prediction, OpenIssue
from gfibot.backend.models import (
    GFIResponse,
    ChatbotSessionCreateRequest,
    ChatbotSessionResponse,
    ChatbotQueryRequest,
    ChatbotQueryResponse,
    ChatMessageModel,
)

api = APIRouter()
logger = logging.getLogger(__name__)

VALID_EXPERTISE_LEVELS = {"beginner", "intermediate", "advanced"}


def generate_initial_greeting(expertise_level: str, repo_name: Optional[str] = None) -> str:
    repo_ctx = f" for repository '{repo_name}'" if repo_name else ""
    if expertise_level == "beginner":
        return (
            f"Hello! 👋 Welcome to GFI-Bot Help Chatbot{repo_ctx}. "
            "I'm here to assist you as you begin your open-source journey. "
            "You can ask me how to find Good First Issues (GFIs), how to choose beginner-friendly projects, "
            "or how GFI-Bot helps newcomers get started!"
        )
    elif expertise_level == "intermediate":
        return (
            f"Hi there! Welcome to GFI-Bot Help Chatbot{repo_ctx}. "
            "I can help you filter projects by responsiveness, analyze issue close times, "
            "and navigate recommended Good First Issues efficiently."
        )
    else:  # advanced
        return (
            f"Welcome to GFI-Bot Technical Assistance{repo_ctx}. "
            "I can provide technical details regarding GFI-Bot GitHub App integration, "
            "`.github/gfibot.yaml` configuration schemas, ML prediction thresholds, and RecGFI model performance."
        )


def generate_chatbot_response(
    query: str, expertise_level: str, repo_name: Optional[str] = None, owner: Optional[str] = None
) -> str:
    q_lower = query.lower()

    # Repository context lookup if available
    repo_stats_summary = ""
    if repo_name and owner:
        try:
            gfi_query = GfiQueries.objects(Q(name=repo_name) & Q(owner=owner)).first()
            if gfi_query:
                gfi_count = Prediction.objects(
                    Q(name=repo_name) & Q(owner=owner) & Q(state="open") & Q(probability__gte=0.5)
                ).count()
                repo_stats_summary = (
                    f" (Stats for {owner}/{repo_name}: {gfi_count} recommended Good First Issues currently available)."
                )
        except Exception as e:
            logger.debug(f"Repo lookup failed for {owner}/{repo_name}: {e}")

    # Keyword routing & expertise level adaptation
    if any(k in q_lower for k in ["what is gfi", "good first issue", "gfi-bot", "how it works", "overview"]):
        if expertise_level == "beginner":
            return (
                "GFI-Bot is an AI/ML-powered assistant that scans GitHub repositories to automatically identify "
                "and label 'Good First Issues' (GFIs)—tasks that are beginner-friendly and great for your first open-source contribution!"
                + repo_stats_summary
            )
        elif expertise_level == "intermediate":
            return (
                "GFI-Bot evaluates open issues using machine learning models (RecGFI) trained on historical issue resolution data. "
                "It ranks issues by GFI probability score and measures repository health metrics like maintainer response time."
                + repo_stats_summary
            )
        else:
            return (
                "GFI-Bot comprises a data collection pipeline (`gfibot.data`), ML recommendation engine (`gfibot.model`), "
                "RESTful backend (`gfibot.backend`), and GitHub App webhook integration (`.github/gfibot.yaml`)."
                + repo_stats_summary
            )

    if any(k in q_lower for k in ["config", "configuration", "yaml", "gfibot.yaml", "setting", "threshold"]):
        if expertise_level == "beginner":
            return (
                "Maintainers can add a `.github/gfibot.yaml` file to their repository to control how GFI-Bot works, "
                "such as setting minimum confidence scores or custom labels."
            )
        elif expertise_level == "intermediate":
            return (
                "The `.github/gfibot.yaml` config allows maintainers to set `newcomer_commit_threshold` (1-5 commits), "
                "`probability_threshold` (e.g. 0.5), `gfi_labels`, and `target_issue_labels`."
            )
        else:
            return (
                "Key `.github/gfibot.yaml` parameters:\n"
                "- `newcomer_commit_threshold`: Integer (1-5, default 3) for contributor qualification.\n"
                "- `probability_threshold`: Float (0.0-1.0) cutoff for automated labeling.\n"
                "- `target_issue_labels`: List of pre-requisite triage labels.\n"
                "- `gfi_labels`: Applied labels (e.g., ['good first issue']).\n"
                "- `comment_enabled`: Boolean toggle for automated issue comments."
            )

    if any(k in q_lower for k in ["find issue", "how to contribute", "start", "onboard", "first issue"]):
        if expertise_level == "beginner":
            return (
                "To get started: 1. Explore candidate projects on the GFI-Bot portal. "
                "2. Filter by your preferred programming language. "
                "3. Pick an issue with a high GFI probability score and leave a polite comment asking to work on it!"
            )
        else:
            return (
                "You can filter repositories on the GFI-Bot web portal by activity, popularity, and newcomer-friendliness. "
                "Look for projects with high median issue response rates for the best onboarding experience."
            )

    if any(k in q_lower for k in ["metric", "auc", "model", "accuracy", "train"]):
        return (
            "GFI-Bot evaluates model performance using Area Under the ROC Curve (AUC) on historical resolved issues. "
            "Models are periodically retrained as new resolved issues accumulate in the repository database."
        )

    # General fallback tailored by level
    if expertise_level == "beginner":
        return (
            f"Thanks for asking! As a beginner, feel free to ask about how to pick a project, what GFI labels mean, "
            f"or how GFI-Bot calculates recommendations{repo_stats_summary}."
        )
    elif expertise_level == "intermediate":
        return (
            f"I'm here to help with repository discovery, metric interpretation, and issue selection{repo_stats_summary}. "
            "What specific aspect of GFI-Bot or project onboarding would you like to explore?"
        )
    else:
        return (
            f"I can assist with GitHub App webhook handling, MongoDB data collection schemas, and RecGFI model parameters{repo_stats_summary}. "
            "Please specify your technical query."
        )


@api.post("/session", response_model=GFIResponse[ChatbotSessionResponse])
def create_session(req: ChatbotSessionCreateRequest):
    """
    Create a new help chatbot session with specified expertise level
    """
    exp_level = req.expertise_level.lower() if req.expertise_level else "beginner"
    if exp_level not in VALID_EXPERTISE_LEVELS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid expertise_level. Must be one of: {sorted(list(VALID_EXPERTISE_LEVELS))}",
        )

    sess_id = uuid.uuid4().hex
    now = datetime.utcnow()

    greeting_content = generate_initial_greeting(exp_level, req.repo_name)
    initial_msg = ChatMessage(role="assistant", content=greeting_content, timestamp=now)

    session_doc = ChatbotSession(
        session_id=sess_id,
        user_id=req.user_id,
        expertise_level=exp_level,
        repo_name=req.repo_name,
        owner=req.owner,
        messages=[initial_msg],
        created_at=now,
        updated_at=now,
    )
    session_doc.save()

    msg_models = [
        ChatMessageModel(role=m.role, content=m.content, timestamp=m.timestamp) for m in session_doc.messages
    ]
    return GFIResponse(
        result=ChatbotSessionResponse(
            session_id=session_doc.session_id,
            user_id=session_doc.user_id,
            expertise_level=session_doc.expertise_level,
            repo_name=session_doc.repo_name,
            owner=session_doc.owner,
            messages=msg_models,
            created_at=session_doc.created_at,
            updated_at=session_doc.updated_at,
        )
    )


@api.get("/session/{session_id}", response_model=GFIResponse[ChatbotSessionResponse])
def get_session(session_id: str):
    """
    Retrieve chatbot session and message history by session_id
    """
    session_doc: Optional[ChatbotSession] = ChatbotSession.objects(session_id=session_id).first()
    if not session_doc:
        raise HTTPException(status_code=404, detail="Chatbot session not found")

    msg_models = [
        ChatMessageModel(role=m.role, content=m.content, timestamp=m.timestamp) for m in session_doc.messages
    ]
    return GFIResponse(
        result=ChatbotSessionResponse(
            session_id=session_doc.session_id,
            user_id=session_doc.user_id,
            expertise_level=session_doc.expertise_level,
            repo_name=session_doc.repo_name,
            owner=session_doc.owner,
            messages=msg_models,
            created_at=session_doc.created_at,
            updated_at=session_doc.updated_at,
        )
    )


@api.post("/query", response_model=GFIResponse[ChatbotQueryResponse])
def query_chatbot(req: ChatbotQueryRequest):
    """
    Query the help chatbot within an existing session
    """
    session_doc: Optional[ChatbotSession] = ChatbotSession.objects(session_id=req.session_id).first()
    if not session_doc:
        raise HTTPException(status_code=404, detail="Chatbot session not found")

    now = datetime.utcnow()
    user_msg = ChatMessage(role="user", content=req.message, timestamp=now)
    session_doc.messages.append(user_msg)

    reply_text = generate_chatbot_response(
        query=req.message,
        expertise_level=session_doc.expertise_level,
        repo_name=session_doc.repo_name,
        owner=session_doc.owner,
    )
    assistant_msg = ChatMessage(role="assistant", content=reply_text, timestamp=now)
    session_doc.messages.append(assistant_msg)

    session_doc.updated_at = now
    session_doc.save()

    history_models = [
        ChatMessageModel(role=m.role, content=m.content, timestamp=m.timestamp) for m in session_doc.messages
    ]

    return GFIResponse(
        result=ChatbotQueryResponse(
            session_id=session_doc.session_id,
            reply=reply_text,
            expertise_level=session_doc.expertise_level,
            history=history_models,
        )
    )


@api.delete("/session/{session_id}", response_model=GFIResponse[bool])
def delete_session(session_id: str):
    """
    Delete a chatbot session
    """
    session_doc: Optional[ChatbotSession] = ChatbotSession.objects(session_id=session_id).first()
    if not session_doc:
        raise HTTPException(status_code=404, detail="Chatbot session not found")
    session_doc.delete()
    return GFIResponse(result=True)
