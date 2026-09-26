# Physical bank routing reinforcement

Verified two- and 64-column routing revisions, rejected spacing control,
48 audited DC records across original/intermediate/selected designs (original
records are in the dependency checkpoint), 13 local-wire controls and a bounded
coupled reset diagnostic. No full-readout accuracy pass is claimed.

Every archive member and numbered part has been read back and hash-verified.
Concatenate parts in order and restore into an empty scratch directory. Do not
unpack archived source snapshots over current work. The manifests of the prior
capture-bank and bank-routing checkpoints are recorded as dependencies.

See [measurements and reproduction](../../docs/bank-reinforcement.md).
