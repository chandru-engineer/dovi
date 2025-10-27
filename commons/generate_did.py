import json
import secrets
import base64
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from commons.s3_client import S3Client
from users.models import DIDKey

def generate_did_document(user=None, base_domain="did.dholakpur.fun"):
    """
    Generate a DID document, store private key in DB, upload DID document to S3.
    """
    # 1️⃣ Generate 16-digit ID
    raw_id = str(secrets.randbelow(10**16)).zfill(16)
    formatted_id = f"{raw_id[:4]}-{raw_id[4:8]}-{raw_id[8:12]}-{raw_id[12:]}"

    # 2️⃣ Generate Ed25519 key pair
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    # 3️⃣ Serialize keys
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()
    )
    private_key_b64 = base64.urlsafe_b64encode(private_bytes).decode("utf-8")

    public_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw
    )
    public_key_b64 = base64.urlsafe_b64encode(public_bytes).decode("utf-8")

    # 4️⃣ Construct DID and document URL
    did = f"did:web:{base_domain}:did:{formatted_id}"
    key_id = f"{did}#key-1"
    document_url = f"https://{base_domain}/did/{formatted_id}/did.json"

    # 5️⃣ Build DID Document
    did_document = {
        "@context": ["https://www.w3.org/ns/did/v1"],
        "id": did,
        "verificationMethod": [
            {
                "id": key_id,
                "type": "Ed25519VerificationKey2018",
                "controller": did,
                "publicKeyBase64": public_key_b64
            }
        ],
        "authentication": [key_id],
        "assertionMethod": [key_id],
        "documentUrl": document_url
    }

    # 6️⃣ Upload DID Document to S3
    s3_client = S3Client()
    s3_key = f"did/{formatted_id}/did.json"
    s3_client.upload_json(s3_key, did_document)

    # 7️⃣ Store private key in DB
    DIDKey.objects.create(
        user=user,
        did=did,
        private_key_b64=private_key_b64,
        public_key_b64=public_key_b64
    )

    print(f"✅ DID: {did}")
    print(f"🌐 Hosted URL: {document_url}")
    print("📄 DID Document:\n", json.dumps(did_document, indent=2))

    return did
