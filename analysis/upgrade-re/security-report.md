# OEM upgrade signature/security analysis

## VERIFIED

- The `upg` executable directly imports and calls the security wrapper family at the recorded call sites.
- `ATP_SEC_VerifyData` has a checked-length path, calls `ATP_SEC_DigestDataEx`, and then dispatches through a context function pointer; the indirect target is not guessed.
- `ATP_SEC_CreateSignatureContext` allocates 36 bytes, stores input fields and callback/context pointers, and selects mode-dependent constants including `0x80000`, `0x10000`, `672`, and `4`.
- `libmsgapi.so` imports CyaSSL RSA, SHA-256, and MD5 primitives.
- Static key/certificate path strings are: `/etc/root.pem`, `/etc/servercert.pem`, `/etc/serverkey.pem`.

### Wrapper ranges

| Function | Address | Size |
|---|---:|---:|
| `ATP_SEC_VerifyDataEx` | `0x14d2c` | `172` |
| `ATP_SEC_VerifyData` | `0x14648` | `204` |
| `ATP_SEC_CreateSignatureContext` | `0x14be8` | `324` |

## INFERRED

- Hash algorithm: **SHA-256 candidate** — libmsgapi imports CyaSSL_SHA256_Init/Update/Final alongside security wrappers; direct resolution of the VerifyData context callback is unavailable.
- Signature family: **RSA candidate** — libmsgapi imports CyaSSL_RSA_verify, CyaSSL_RSA_size, and RSA key-management primitives.
- Embedded uImage header and payload CRC32 are VERIFIED by the repository firmware validator; OEM outer-container checksum coverage remains UNKNOWN.

## UNKNOWN / BLOCKED

- `rsa_key_size`: UNKNOWN: CyaSSL_RSA_size is imported, but no verified result or fixed modulus length is exposed by the traced wrapper.
- `signature_length_and_encoding`: UNKNOWN: no direct signature-buffer format or length field was resolved through the indirect context callback.
- `padding_scheme`: UNKNOWN: RSA primitive presence does not distinguish PKCS#1 v1.5 from PSS.
- `hashed_byte_range`: UNKNOWN: ATP_SEC_VerifyData adjusts caller length fields and calls ATP_SEC_DigestDataEx, but the ultimate callback arguments and header exclusions are unresolved.
- `signature_storage`: UNKNOWN: no embedded public key/signature object was identified; certificate/key paths are runtime filesystem paths and are not proven firmware-update keys.
- `failure_behavior`: INFERRED only: wrapper returns error values and `upg` contains Verify head/signature-related error strings; exact recovery/rollback actions remain unresolved.
- `outer_container_checksum`: UNKNOWN: the existing firmware parser verifies embedded uImage header/data CRC32, but no OEM outer-container checksum or coverage has been identified.

No private key is generated or extracted. This report does not bypass or weaken any signature check.
