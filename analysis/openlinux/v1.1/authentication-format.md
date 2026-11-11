# V1.1 authentication format

Status: **BLOCKED**.

The static call graph proves use of security wrappers and linked RSA/SHA-256
primitives, but it does not resolve the indirect signature-context callback.
The following remain UNKNOWN:

- RSA modulus and signature size;
- signature encoding and padding mode;
- exact digest algorithm for the update path;
- signed byte range and excluded fields;
- embedded versus filesystem-loaded public key;
- outer-container checksum and coverage;
- failure/rollback result codes.

The only independently verified integrity values are the embedded uImage
header/data CRC32 values. They are not an OEM package signature. No verifier
or signing tool is implemented because the required public-key and format
inputs are insufficient.
