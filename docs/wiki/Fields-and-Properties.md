# Fields and properties

## Standard properties

Every part has:

| Property | | On the sheet |
|---|---|---|
| **Reference** | `R1`, `U3`; numbered automatically from the symbol's prefix (R, C, L, D, Q, U, …) | yes, bold |
| **Value** | `10 k\ohm`, `100 nF`, `OPA210`, a SPICE source spec | yes |
| **Part number** | manufacturer part / SPICE model name (`BC547`, `1N4148`) | yes, small |

plus the symbol's own **settings** (diode *kind*, gate *inputs*, register *bits*, …; see the
[Symbol library](Symbol-Library.md)). Settings marked *shape* change the drawing.

Hide a part's labels with *Labels* in the inspector (`hide_labels`). Drag the label block on the sheet to move it
(*Reset label* puts it back).

## Fields: your own properties

A part can carry any number of extra **fields**: tolerance, voltage rating, power, footprint, supplier, cost,
anything. Each field has a **name**, a **value** and a **show** switch; shown values print under the part's other
labels.

**In the editor** (Properties pane, *Fields*):

- the chips under the list add the fields suggested for that symbol (a resistor suggests Tolerance, Power, Tempco,
  Voltage rating; a capacitor Voltage rating, Tolerance, Dielectric, ESR; …), **+ Field…** adds any other;
- type the name and value; tick the box to show the value on the sheet; × removes it;
- double-click a shown value on the sheet to edit it in place.

**In Python**:

```python
r = s.resistor((100, 60), value='10 k\\ohm',
               fields={'Tolerance': ('1%', True),     # (value, shown)
                       'Power': '0.25 W'})            # hidden
r.field('Power')                  # -> '0.25 W'
r.field('Power', show=True)       # show it
r.field('Footprint', '0603')      # add / change
r.remove_field('Power')
r.fields                          # {'Tolerance': '1%', 'Footprint': '0603'}
```

**In files**: `"fields": [{"name": "Tolerance", "value": "1%", "show": true}]` on the element
([Document format](Document-Format.md)).

## Where fields go

- **Netlists**: JSON netlists carry every field; KiCad netlists write them as component fields (a field named
  `Footprint` becomes the KiCad footprint); SPICE netlists keep them in `*@` comments so a re-import restores them.
- **Imports**: KiCad fields (except Reference / Value / Datasheet / Description) and the footprint come back as fields.
- **Find and replace** searches field values.
- Fields accept [text markup](Text-Markup.md) like every text.
