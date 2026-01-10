- allow shorter words but only if part of spangram
- consider doing spangram finding before full covering?

## Crossing checks with segment variables

A more advanced formulation could introduce segment variables that explicitly track which segments are "active" and use geometric constraints:

```
For each potential crossing point (diagonal adjacency in grid):
    Let seg_a, seg_b be the two diagonal segments through that point
    At most one of seg_a, seg_b can be active
```
