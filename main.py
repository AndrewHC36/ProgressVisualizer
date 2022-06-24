import tkinter as tk
import tkinter.font as tkf
from datetime import datetime
from typing import Optional

import backend


# (HORIZONTAL) BAR CHART
def bar_chart(data: dict[str, int], c: tk.Canvas, new=True, items: Optional[list]=None):
	"""
	:param data: Same as pie chart
	"""
	pad = 20
	total = sum(list(data.values()))

	# store the canvas item instances for updating them later
	bar_items = items if not new else []

	inc = pad
	for ind, k in enumerate(data):
		if ind != len(data)-1:
			length = int((c.winfo_reqwidth()-2*pad)*(data[k]/total))
			if new:
				bar = c.create_rectangle(inc, pad, inc+length, 80+pad, fill=k, tags="")
				txt = c.create_text(inc+length/2, 40+pad, text=str(p)+"%" if (p := int(100*data[k]/total)) > 5 else "", font=("Arial", 16))
				bar_items.append(bar)
				bar_items.append(txt)
			else:
				c.coords(bar_items[ind*2+0], inc, pad, inc+length, 80+pad)
				c.coords(bar_items[ind*2+1], inc+length/2, 40+pad)
				c.itemconfigure(bar_items[ind*2+1], text=str(p)+"%" if (p := int(100*data[k]/total)) > 5 else "")
			inc += length
		else:
			# last one
			if new:
				bar = c.create_rectangle(inc, pad, c.winfo_reqwidth()-pad, 80+pad, fill=k)
				txt = c.create_text((inc+c.winfo_reqwidth()-pad)/2, 40+pad, text=str(p)+"%" if (p := int(100*data[k]/total)) > 5 else "", font=("Arial", 16))
				bar_items.append(bar)
				bar_items.append(txt)
			else:
				c.coords(bar_items[ind*2+0], inc, pad, c.winfo_reqwidth()-pad, 80+pad)
				c.coords(bar_items[ind*2+1], (inc+c.winfo_reqwidth()-pad)/2, 40+pad)
				c.itemconfigure(bar_items[ind*2+1], text=str(p)+"%" if (p := int(100*data[k]/total)) > 5 else "")

	return bar_items


# PIE CHART reference: http://www.codingandanalytics.com/2018/04/blog-post_17.html
def pie_chart(data: dict[str, int], c: tk.Canvas, new=True, items: Optional[list]=None):
	"""
	:param data: A dictionary with a key of color "#FFFFFF" and the ratio in integer
	"""
	size = 150
	total = sum(list(data.values()))

	# store the canvas item instances for updating them later
	pie_items = items if not new else []

	coord = (c.winfo_reqwidth()/2-size, 2*c.winfo_reqheight()/3-size, c.winfo_reqwidth()/2+size, 2*c.winfo_reqheight()/3+size)

	inc = 0
	for ind, k in enumerate(data):
		if ind != len(data)-1:
			arc_len = int(360*(data[k]/total))
			if new:
				arc = c.create_arc(coord, fill=k, outline="#000000", start=inc, extent=arc_len)
				pie_items.append(arc)
			else:
				c.itemconfigure(pie_items[ind], start=inc, extent=arc_len)
			inc += arc_len
		else:
			# last part (to make the pie chart look complete, preventing the annoying small gap for the last part)
			arc_len = 360-inc
			if new:
				arc = c.create_arc(coord, fill=k, outline="#000000", start=inc, extent=arc_len)
				pie_items.append(arc)
			else:
				c.itemconfigure(pie_items[ind], start=inc, extent=arc_len)

	return pie_items


# -- initial setup --

root = tk.Tk()
root.title("Google Task List - Progress Visualizer")
root.state('zoomed')

tk_grid = tk.Entry()

# -- header controls --

task_data: dict[str, list[tuple[bool, datetime, datetime]]] = backend.retrieve_task_data("credentials.json")

selc = tk.StringVar()  # tracker variable for the current selection of OptionMenu
selc.set(list(task_data.keys())[0])

mo_lbl = tk.StringVar()
wk_lbl = tk.StringVar()
dy_lbl = tk.StringVar()

monthly_dt = {}
weekly_dt = {}
daily_dt = {}

c_monthly = tk.Canvas(root, width=500, height=500, bg='white')
c_weekly = tk.Canvas(root, width=500, height=500, bg='white')
c_daily = tk.Canvas(root, width=500, height=500, bg='white')
i_monthly: tuple[list, list]
i_weekly: tuple[list, list]
i_daily: tuple[list, list]

def update_timef():
	global task_data, monthly_dt, weekly_dt, daily_dt, c_monthly, c_weekly, c_daily, i_monthly, i_weekly, i_daily

	task_data = backend.retrieve_task_data("credentials.json")

	res = backend.process_tasks(task_data[selc.get()])
	mo_lbl.set(f"Monthly Progress [{res['monthly'][0]}]")
	wk_lbl.set(f"Weekly Progress [{res['weekly'][0]}]")
	dy_lbl.set(f"Daily Progress [{res['daily'][0]}]")

	mapper = {"unfinished": "#FFAA00", "soon": "#FF8833", "overdue": "#FF0000", "finished": "#00FF00"}
	monthly_dt = {mapper[k]: res["monthly"][1][k] for k in res["monthly"][1]}
	weekly_dt = {mapper[k]: res["weekly"][1][k] for k in res["weekly"][1]}
	daily_dt = {mapper[k]: res["daily"][1][k] for k in res["daily"][1]}

	# assuming the charts are initially created somewhere else
	if "i_monthly" in globals():
		bar_chart(monthly_dt, c_monthly, new=False, items=i_monthly[0])
		pie_chart(monthly_dt, c_monthly, new=False, items=i_monthly[1])
	if "i_weekly" in globals():
		bar_chart(weekly_dt, c_weekly, new=False, items=i_weekly[0])
		pie_chart(weekly_dt, c_weekly, new=False, items=i_weekly[1])
	if "i_daily" in globals():
		bar_chart(daily_dt, c_daily, new=False, items=i_daily[0])
		pie_chart(daily_dt, c_daily, new=False, items=i_daily[1])


selc.trace("w", lambda *_: update_timef())
opt = tk.OptionMenu(root, selc, *list(task_data.keys()))
opt.config(width=50)
opt.grid(row=0, column=0)

btn = tk.Button(root, text="Refresh", command=update_timef)
btn.grid(row=0, column=1)

# -- charts --

update_timef()
chart_lbl_f = tkf.Font(size=16, family="Georgia")

i_monthly = (bar_chart(monthly_dt, c_monthly), pie_chart(monthly_dt, c_monthly))
i_weekly = (bar_chart(weekly_dt, c_weekly), pie_chart(weekly_dt, c_weekly))
i_daily = (bar_chart(daily_dt, c_daily), pie_chart(daily_dt, c_daily))

tk.Label(root, textvariable=mo_lbl, font=chart_lbl_f).grid(row=1,column=0)
c_monthly.grid(row=2,column=0)

tk.Label(root, textvariable=wk_lbl, font=chart_lbl_f).grid(row=1,column=1)
c_weekly.grid(row=2,column=1)

tk.Label(root, textvariable=dy_lbl, font=chart_lbl_f).grid(row=1,column=2)
c_daily.grid(row=2,column=2)


root.mainloop()


"""
Progress Visualizer - Task List

- Will have a daily, weekly, and monthly section (annual if needed)
	- Each will have two graphs with each of their respective tasks
		- A progress (horizontal bar) graph
		- A pie chart graph to show the progress
- Each chart will show these components
	- Finished (tasks marked complete) [GREEN]
	- Overdue (if task is deadlined) [RED]
	- Unfinished (due within set timelength) [BROWN]
		- Daily: 1 hour
		- Weekly: 1 Day (24 hrs)
		- Monthly: 1 Week (7 days)
	- Unfinished [ORANGE]
- Each chart is set by each day/week/month
- Pick which task list to check

- Each chart will only account tasks within each of its timeframe (when deadline is provided, otherwise include it)
-- Overdue is a weird exception, it will stay included even if its passed the graph's timeframe until its finished

"""
