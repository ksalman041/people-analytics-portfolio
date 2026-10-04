# Visual positions

Power BI: select a visual > Format > General > Properties > Size and position, then type these values.
Visuals sit 4 px inside their card. Canvas: 1280 x 720 (Format page > Canvas settings > 16:9).

## Board Summary  (`backgrounds/1_board_summary.png`)

| Slot | Visual | X | Y | Width | Height | Title (states the message) |
|---|---|---|---|---|---|---|
| title | Textbox | 24 | 24 | 640 | 48 | Page title + 'Vltava Market Group · synthetic data' |
| filters | Slicers | 856 | 24 | 400 | 48 | One filter row: Month · Division · Legal entity |
| K1 | Card (new) | 28 | 92 | 184 | 96 | Headcount |
| K2 | Card (new) | 236 | 92 | 184 | 96 | Hires (R12) |
| K3 | Card (new) | 444 | 92 | 184 | 96 | Turnover (R12) |
| K4 | Card (new) | 652 | 92 | 184 | 96 | Voluntary turnover (R12) |
| K5 | Card (new) | 860 | 92 | 184 | 96 | Women in leadership |
| K6 | Card (new) | 1068 | 92 | 184 | 96 | Gender pay gap (raw, mean) |
| A | Line chart (small multiples by entity) | 28 | 212 | 792 | 228 | Headcount +14% in two years - all of it in Prague |
| B | Textbox | 844 | 212 | 408 | 228 | Three key messages for the Board |
| C | Bar chart, emphasis | 28 | 464 | 600 | 228 | Operations and Technology lose 1 in 5 people a year |
| D | Clustered bar: AC vs PY | 652 | 464 | 600 | 228 | Prague +9 people vs last year; other entities flat |

## Movement & Attrition  (`backgrounds/2_movement_attrition.png`)

| Slot | Visual | X | Y | Width | Height | Title (states the message) |
|---|---|---|---|---|---|---|
| title | Textbox | 24 | 24 | 640 | 48 | Page title + 'Vltava Market Group · synthetic data' |
| filters | Slicers | 856 | 24 | 400 | 48 | One filter row: Month · Division · Legal entity |
| A | Waterfall | 28 | 92 | 744 | 336 | Headcount bridge, last 12 months: hires outpaced leavers |
| B | Line chart, emphasis | 796 | 92 | 456 | 336 | Operations turnover runs well above the company |
| C | Bar chart | 28 | 452 | 360 | 240 | Personal reasons drive 3 in 10 exits |
| D | Bar chart, emphasis | 412 | 452 | 360 | 240 | 60% of Operations leavers quit in year one |
| E | Bar chart, emphasis | 796 | 452 | 456 | 240 | First-year turnover is twice the later-year rate |

## Diversity & Pay  (`backgrounds/3_diversity_pay.png`)

| Slot | Visual | X | Y | Width | Height | Title (states the message) |
|---|---|---|---|---|---|---|
| title | Textbox | 24 | 24 | 640 | 48 | Page title + 'Vltava Market Group · synthetic data' |
| filters | Slicers | 856 | 24 | 400 | 48 | One filter row: Month · Division · Legal entity |
| K1 | Card (new) | 28 | 92 | 288 | 96 | Women, all staff |
| K2 | Card (new) | 340 | 92 | 288 | 96 | Women in leadership |
| K3 | Card (new) | 652 | 92 | 288 | 96 | Pay gap, raw (mean) |
| K4 | Card (new) | 964 | 92 | 288 | 96 | Pay gap, like-for-like |
| A | 100% stacked bar | 28 | 212 | 600 | 480 | Women thin out above grade G4 |
| B | Clustered bar: ours vs Eurostat | 652 | 212 | 600 | 228 | Our raw gaps sit below each country's financial sector |
| C | Table (n<5 suppressed) | 652 | 464 | 600 | 228 | Like-for-like gaps stay under the 5% Directive trigger |

## Data Quality  (`backgrounds/4_data_quality.png`)

| Slot | Visual | X | Y | Width | Height | Title (states the message) |
|---|---|---|---|---|---|---|
| title | Textbox | 24 | 24 | 640 | 48 | Page title + 'Vltava Market Group · synthetic data' |
| filters | Slicers | 856 | 24 | 400 | 48 | One filter row: Month · Division · Legal entity |
| K1 | Card (new) | 28 | 92 | 288 | 96 | Files loaded |
| K2 | Card (new) | 340 | 92 | 288 | 96 | Rows loaded |
| K3 | Card (new) | 652 | 92 | 288 | 96 | Rule exceptions |
| K4 | Card (new) | 964 | 92 | 288 | 96 | Rows excluded |
| A | Bar chart | 28 | 212 | 600 | 268 | Non-standard location labels are the most common issue |
| B | Column chart | 652 | 212 | 600 | 268 | Exceptions by monthly file |
| C | Table | 28 | 504 | 1224 | 188 | Exception detail: rule, file, person, action taken |
