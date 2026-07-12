# Theory guard

| ID | Severity | Invariant | Evidence |
| --- | --- | --- | --- |
| PF-001 | BLOCKER | The voltage source drives the right electrode and its return terminates at ground. | semantic contract plus source/electrode zoom |
| PF-001B | BLOCKER | The sample and cantilever remain electrically floating; the top jig cannot read as an electrical contact. | semantic contract plus jig/sample zoom |
| PF-001C | BLOCKER | The ground symbol belongs only to the source return, never to the sample, cantilever, or electrode. | semantic contract plus source/electrode zoom |
| PF-002 | BLOCKER | Coulomb force points away from the right electrode. | inherited TeX assertion plus object/relation crop |
| PF-003 | BLOCKER | Cantilever and electrode remain separated by the labelled air gap. | source token test plus panel crop |
| PF-004 | BLOCKER | Machine validity is not publication acceptance. | generated receipt and pending human verdict |
