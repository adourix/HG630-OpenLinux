# V1.0 signature and integrity analysis

## VERIFIED

- The preserved `upg` executable calls the `ATP_SEC_*` security wrapper family.
- `libmsgapi.so` imports RSA, SHA-256, and MD5 primitives, including
  `CyaSSL_RSA_verify`, `CyaSSL_RSA_size`, `CyaSSL_SHA256_Init/Update/Final`,
  and MD5 routines.
- `ATP_SEC_VerifyData` includes checked-length and digest-processing paths, but
  indirect context dispatches prevent a complete end-to-end data-flow proof.
- The embedded uImage header/data CRC32 values are independently verified.

## UNKNOWN / BLOCKED

- RSA modulus/key size, signature length and encoding, and PKCS#1 v1.5 versus
  PSS are unresolved.
- The exact signed byte range and header exclusions are unresolved.
- No firmware-update public key or signature object was extracted and no
  legitimate signing credential is available.
- No OEM outer-container checksum or authentication field has been identified.
- Failure, rollback, and recovery behavior are not proven.

Consequently, a Python signature verifier and a signed OEM reconstruction are
BLOCKED. This project does not generate a private key, bypass verification, or
disable the OEM trust path.
