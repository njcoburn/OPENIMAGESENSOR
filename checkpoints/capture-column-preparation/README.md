# Capture column preparation

Prepared schematic subcircuits and conditional MIM capacitor dimensions; no
physical layout or new simulation result. See
[`docs/capture-column-preparation.md`](../../docs/capture-column-preparation.md)
for scope, model limitations, reproduction and remaining checks.

`preparation.json` records hashes of the three archived inputs (`source.spice`,
`model.ngspice`, `rules.rb`) and four generated subcircuit files. The full-row
source deck is retained for the 64-column equivalence audit; its external file
dependencies remain in the prior grid-readout checkpoint. PDK model and rule
files retain their original notices.

Validation completed: expanded all 512 column elements and six shared fixture
elements back to the original flat records; checked 24 serialized capacitor
instances and their nominal capacitance; rejected an intentionally changed
column-63 capture control; verified hashes and byte-identical regeneration from
the archived inputs. These checks do not substitute for EDA verification.
