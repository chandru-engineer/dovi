import didkit
import json
from datetime import datetime, timedelta

def issue_vc_with_didkit(post, ministry_did, key_json):
    """
    post: dict with 'id', 'title', 'content'
    ministry_did: DID string of ministry
    key_json: JSON string of DIDKit key (Ed25519)
    """

    issuance_date = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    expiration_date = (datetime.utcnow() + timedelta(days=365)).replace(microsecond=0).isoformat() + "Z"

    vc = {
        "@context": [
            "https://www.w3.org/2018/credentials/v1",
            "https://schema.credissuer.com/templates/GovernmentPublicationCredential/context.json",
            "https://w3id.org/security/suites/ed25519-2020/v1"
        ],
        "id": f"urn:uuid:{post['id']}",
        "type": ["VerifiableCredential", "GovernmentPublicationCredential"],
        "issuer": ministry_did,
        "issuanceDate": issuance_date,
        "expirationDate": expiration_date,
        "credentialSubject": {
            "id": f"did:web:did.dholakpur.fun:{post['id']}",
            "type": "GovernmentPublicationCredential",
            "title": post['title'],
            "content": post['content']
        }
    }

    # Issue (sign) the VC
    vc_json = json.dumps(vc)
    proof_options = json.dumps({
        "proofPurpose": "assertionMethod",
        "verificationMethod": f"{ministry_did}#keys-1"
    })

    signed_vc = didkit.issue_credential(vc_json, proof_options, key_json)
    signed_vc_dict = json.loads(signed_vc)

    return signed_vc_dict


if __name__ == "__main__":
    # Generate a temporary Ed25519 key for testing
    key_json = didkit.generate_ed25519_key()
    ministry_did = 'did:web:did.dholakpur.fun:did:4545-9443-8403-6317'

    # Example test post
    test_post = {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "title": "Test Government Circular",
        "content": "This is a test content for issuing VC."
    }

    # Issue the VC
    signed_vc = issue_vc_with_didkit(test_post, ministry_did, key_json)

    # Print the signed VC JSON
    print(json.dumps(signed_vc, indent=2))
