import openpyxl
wb = openpyxl.load_workbook(
    '1_Input/ExistTing Projects OBS_83410775-PRJ-CAN-EN - URS Generic WBS OBS and RACI Matrix.xlsx',
    data_only=True)
ws = wb['Generic RACI']
print('=== ALL ROLES in Generic RACI ===')
for i, row in enumerate(ws.iter_rows(min_row=1, max_row=123, values_only=True)):
    vals = [str(c).strip() for c in row[:5] if c is not None and str(c).strip()]
    if vals and not vals[0].startswith('Generic') and vals[0] != '-':
        print('R%d: %s' % (i+1, ' | '.join(vals)))
