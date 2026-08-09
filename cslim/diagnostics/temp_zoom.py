import sys
with open('visualize_month4_video1.py', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace(
    'xaxis_rangeslider_visible=False,',
    "xaxis_rangeslider_visible=False,\n        xaxis_range=['2016-04-10', '2016-05-13'],"
)
content = content.replace('visualize_month4_video1.html', 'visualize_month4_video1_zoomed.html')
with open('visualize_month4_video1_zoomed.py', 'w', encoding='utf-8') as f:
    f.write(content)
