import json
import hashlib
import uuid
import re
from datetime import datetime, timedelta

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from users.models import UserProfile, UserType
from vcs.models import Post

import json
import hashlib
import uuid
from datetime import datetime, timedelta
import openai

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from users.models import UserProfile, UserType
from vcs.models import Post
from difflib import SequenceMatcher
from dovi_api.settings import OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY


class CreateMinistryPostView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        profile = UserProfile.objects.get(user=user)
        if profile.user_type != UserType.MINISTRY.value:
            return Response({"error": "Only ministry users can create ministry posts"}, status=status.HTTP_403_FORBIDDEN)
        
        title = request.data.get("title")
        content = request.data.get("content")
        if not title or not content:
            return Response({"error": "Title and content are required"}, status=status.HTTP_400_BAD_REQUEST)

        # Compute hash of title + content
        content_str = f"{title}|{content}"
        content_hash = hashlib.sha256(content_str.encode("utf-8")).hexdigest()

        # Simulated credential ID
        credential_id = f"did:dholakpur:fun:vc:{uuid.uuid4()}"

        # Create the post with simulated VC and proof
        post = Post.objects.create(
            author=user,
            title=title,
            content=content,
            post_type='government',
            is_published=True,
            vc_status='issued',
            vc_issuer_did=profile.did_url,
            vc_proof={
                "credential_id": credential_id,
                "content_hash": content_hash
            },
            vc_type="GovernmentPublicationCredential",
            vc_issuance_date=datetime.utcnow(),
            vc_expiration_date=datetime.utcnow() + timedelta(days=365),
            proof={
                "is_verified_issuer": True,
                "content_integrity": True,
                "sentiment": "neutral",
                "checked_at": datetime.utcnow().isoformat() + "Z",
                "notes": "Ministry-authoritative content"
            }
        )

        return Response({
            "message": "Ministry post created (simulated VC & proof)",
            "post_id": str(post.id),
            "vc_proof": post.vc_proof,
            "proof": post.proof
        }, status=status.HTTP_201_CREATED)



class CreatePublisherPostView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        profile = UserProfile.objects.get(user=user)
        if profile.user_type != UserType.PUBLISHER.value:
            return Response({"error": "Only publisher users can create posts"}, status=status.HTTP_403_FORBIDDEN)
        
        title = request.data.get("title")
        content = request.data.get("content")
        if not title or not content:
            return Response({"error": "Title and content are required"}, status=status.HTTP_400_BAD_REQUEST)

        # Compute hash of publisher content
        content_str = f"{title}|{content}"
        content_hash = hashlib.sha256(content_str.encode("utf-8")).hexdigest()
        credential_id = f"did:dholakpur:fun:vc:{uuid.uuid4()}"

        # Fetch all ministry-authoritative posts
        ministry_posts = Post.objects.filter(vc_status='issued', post_type='government')
        related_vc_ids = []
        ministry_data = []

        for p in ministry_posts:
            ministry_hash = p.vc_proof.get("content_hash", "")
            ministry_cred_id = p.vc_proof.get("credential_id", "")
            ministry_data.append({
                "title": p.title,
                "content": p.content,
                "content_hash": ministry_hash,
                "credential_id": ministry_cred_id
            })
            # Collect matching ministry VC IDs
            if ministry_hash == content_hash:
                related_vc_ids.append(ministry_cred_id)

        # Prepare prompt for LLM
        prompt = f"""
        You are a content verification assistant.
        Analyze the following publisher content and validate it against authoritative ministry posts.
        Return a JSON with fields:
        - is_verified_issuer (true if content matches any ministry post hash, else false)
        - content_integrity (true if content is semantically valid)
        - sentiment (positive/neutral/negative)
        - notes (brief explanation)

        Publisher Content:
        Title: "{title}"
        Content: "{content}"
        Content Hash: {content_hash}

        Ministry Posts Data (hashes, content, credential_id):
        {json.dumps(ministry_data)}
        """

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            llm_output = response['choices'][0]['message']['content']
            proof_data = json.loads(llm_output)
        except Exception as e:
            return Response({"error": f"LLM proof generation failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Add related VC IDs to proof
        proof_data["related_vc_ids"] = related_vc_ids

        # Create publisher post with proof
        post = Post.objects.create(
            author=user,
            title=title,
            content=content,
            post_type='publisher',
            is_published=True,
            vc_status='pending',
            vc_issuer_did=profile.did_url,
            vc_proof={
                "credential_id": credential_id,
                "content_hash": content_hash
            },
            vc_type="PublisherPublicationCredential",
            vc_issuance_date=datetime.utcnow(),
            vc_expiration_date=datetime.utcnow() + timedelta(days=365),
            proof=proof_data
        )

        return Response({
            "message": "Publisher post created with LLM-verified proof",
            "post_id": str(post.id),
            "vc_proof": post.vc_proof,
            "proof": post.proof
        }, status=status.HTTP_201_CREATED)
    



class VerifyContentView(APIView):
    """
    Verify a content's authenticity in the DOVI portal.
    This API compares the submitted content against all ministry-authoritative posts
    and checks for both exact and semantic similarity.
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        title = request.data.get("title", "").strip()
        content = request.data.get("content", "").strip()

        if not content:
            return Response({"error": "Title and content are required"}, status=status.HTTP_400_BAD_REQUEST)

        # Compute content hash
        content_str = f"{title}|{content}"
        content_hash = hashlib.sha256(content_str.encode("utf-8")).hexdigest()

        # Fetch all ministry-authoritative posts
        ministry_posts = Post.objects.filter(vc_status='issued', post_type='government')
        related_vc_ids = []
        ministry_data = []
        best_match = None
        best_score = 0.0

        for p in ministry_posts:
            ministry_hash = p.vc_proof.get("content_hash", "")
            ministry_cred_id = p.vc_proof.get("credential_id", "")
            ministry_content = f"{p.title}|{p.content}"

            # Compute semantic similarity
            similarity = SequenceMatcher(None, content_str.lower(), ministry_content.lower()).ratio()

            ministry_data.append({
                "title": p.title,
                "content": p.content,
                "content_hash": ministry_hash,
                "credential_id": ministry_cred_id,
                "similarity_score": round(similarity, 3)
            })

            # Exact hash match
            if ministry_hash == content_hash:
                related_vc_ids.append(ministry_cred_id)

            # Track best semantic match
            if similarity > best_score:
                best_score = similarity
                best_match = ministry_cred_id

        # Add near match if high semantic similarity (>85%)
        if not related_vc_ids and best_score >= 0.85 and best_match:
            related_vc_ids.append(best_match)

        # Prepare LLM validation
        prompt = f"""
        You are a trusted AI verifier for the DOVI portal.
        Verify the following content against authoritative ministry publications.
        Return a JSON with fields:
        - is_verified_issuer (true if content matches or is a verified derivative)
        - content_integrity (true if the content is semantically valid)
        - sentiment (positive/neutral/negative)
        - notes (brief explanation)
        Focus on authenticity and integrity, not tone.

        Submitted Content:
        Title: "{title}"
        Content: "{content}"
        Hash: {content_hash}

        Ministry Data (top posts with hash & similarity):
        {json.dumps(ministry_data[:5], indent=2)}
        """

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            llm_output = response["choices"][0]["message"]["content"]
            proof_data = json.loads(llm_output)
        except Exception as e:
            return Response({"error": f"AI verification failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Attach related VC IDs and verification timestamp
        proof_data["related_vc_ids"] = related_vc_ids
        proof_data["checked_at"] = datetime.utcnow().isoformat() + "Z"
        proof_data["semantic_similarity"] = round(best_score, 3)

        return Response({
            "message": "Content verification completed",
            "title": title,
            "content": content,
            "proof": proof_data
        }, status=status.HTTP_200_OK)
    


class FetchRelatedDocumentView(APIView):
    """
    Fetch the related authoritative document or VC by its DID identifier.
    Example input:
    {
        "did": "did:dholakpur:fun:vc:cb859bb3-3b44-4e1e-9b10-a00bbb69a334"
    }
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request, did_id):
        did = did_id.strip()
        if not did:
            return Response({"error": "DID identifier is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Validate DID format
        match = re.match(r"^did:dholakpur:fun:vc:([a-f0-9\-]+)$", did)
        if not match:
            return Response({"error": "Invalid DID format"}, status=status.HTTP_400_BAD_REQUEST)

        credential_id = did  # same format stored in vc_proof

        # Search in Post table
        post = Post.objects.filter(vc_proof__credential_id=credential_id).first()
        if not post:
            return Response({"error": "No record found for this DID"}, status=status.HTTP_404_NOT_FOUND)

        # Build the DID Document link (assuming DID registry base URL)
        did_document_url = f"https://did.dholakpur.fun/did/{credential_id.split(':')[-1]}/did.json"

        data = {
            "title": post.title,
            "content": post.content,
            "issuer_did": post.vc_issuer_did,
            "vc_proof": post.vc_proof,
            "vc_type": post.vc_type,
            "vc_status": post.vc_status,
            "issuance_date": post.vc_issuance_date,
            "expiration_date": post.vc_expiration_date,
            "proof": post.proof,
            "did_document_url": did_document_url
        }

        return Response({
            "message": "Related document fetched successfully",
            "did": credential_id,
            "document": data
        }, status=status.HTTP_200_OK)