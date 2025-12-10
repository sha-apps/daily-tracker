import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, datetime
import db
from streamlit_calendar import calendar

# Page Config
st.set_page_config(page_title="Daily Tracker", page_icon="✅", layout="wide")

# Initialize DB
db.init_db()

# Custom CSS for Premium Look
st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    .stButton>button {
        background-color: #ff4b4b;
        color: white;
        border-radius: 20px;
        border: none;
        padding: 10px 24px;
        font-weight: bold;
    }
    .stTextInput>div>div>input {
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# Sidebar
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Daily Tracker", "Calendar", "Analytics"])

if page == "Daily Tracker":
    st.title("📝 Daily Tracker")
    
    # Tabs for Tasks and Deadlines
    tab1, tab2 = st.tabs(["Tasks", "Approaching Deadlines"])
    
    with tab1:
        # Input Form
        with st.expander("Add New Item", expanded=False):
            with st.form("new_task"):
                col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                with col1:
                    task_title = st.text_input("Title")
                with col2:
                    category = st.selectbox("Category", ["🔥 Critical", "📅 Goals", "⚡ Quick Tasks", "🌱 Backlog"])
                with col3:
                    item_type = st.selectbox("Type", ["Task", "Appointment"])
                with col4:
                    due_date = st.date_input("Date", min_value=date.today())
                
                item_time = None
                if item_type == "Appointment":
                    item_time = st.time_input("Time")

                submitted = st.form_submit_button("Add Item")
                if submitted and task_title:
                    db.add_task(task_title, category, due_date, item_type, item_time)
                    st.success(f"{item_type} added!")
                    st.rerun()

        # Date Range Filter
        st.subheader("Your Items")
        
        # Default to today
        today = date.today()
        
        # Date Input for Range
        # st.date_input returns a tuple. If one date is selected, it's (date,). If two, (start, end).
        # We handle both cases to avoid errors during selection.
        date_range = st.date_input("Select Period", value=(today, today), format="YYYY/MM/DD")
        
        start_date = today
        end_date = today

        if isinstance(date_range, tuple):
            if len(date_range) == 2:
                start_date, end_date = date_range
            elif len(date_range) == 1:
                start_date = date_range[0]
                end_date = date_range[0]
        else:
            # Fallback if single date returned (unlikely with range logic but safe)
            start_date = date_range
            end_date = date_range

        tasks = db.get_tasks()
        
        if not tasks.empty:
            # Ensure due_date is datetime for comparison
            tasks['due_date_dt'] = pd.to_datetime(tasks['due_date']).dt.date
            
            # Filter Tasks by Range
            filtered_tasks = tasks[
                (tasks['due_date_dt'] >= start_date) & 
                (tasks['due_date_dt'] <= end_date)
            ]

            # Progress Bars (Only for Tasks, not Appointments)
            all_tasks = tasks[tasks['item_type'] == 'Task']
            filtered_task_items = filtered_tasks[filtered_tasks['item_type'] == 'Task']
            
            # Overall Progress (All Time)
            total_all = len(all_tasks)
            completed_all = len(all_tasks[all_tasks['status'] == 'Completed'])
            progress_all = completed_all / total_all if total_all > 0 else 0
            
            # Selected Period Progress
            total_filtered = len(filtered_task_items)
            completed_filtered = len(filtered_task_items[filtered_task_items['status'] == 'Completed'])
            progress_filtered = completed_filtered / total_filtered if total_filtered > 0 else 0

            col_prog1, col_prog2 = st.columns(2)
            with col_prog1:
                st.caption(f"Overall Progress (All Time): {int(progress_all * 100)}%")
                st.progress(progress_all)
            with col_prog2:
                st.caption(f"Period Progress ({start_date} - {end_date}): {int(progress_filtered * 100)}%")
                st.progress(progress_filtered)

            # Display Tasks by Category
            categories = ["🔥 Critical", "📅 Goals", "⚡ Quick Tasks", "🌱 Backlog"]
            
            cols = st.columns(len(categories))
            
            for i, cat in enumerate(categories):
                with cols[i]:
                    st.markdown(f"### {cat}")
                    cat_tasks = filtered_tasks[filtered_tasks['category'] == cat]
                    for index, row in cat_tasks.iterrows():
                        with st.container():
                            icon = "📌" if row['item_type'] == 'Appointment' else "📝"
                            time_str = f" at {row['item_time']}" if row['item_time'] and row['item_time'] != 'None' else ""
                            
                            col_check, col_text = st.columns([1, 4])
                            with col_check:
                                is_checked = st.checkbox("", value=row['status'] == 'Completed', key=f"check_{row['id']}")
                                if is_checked and row['status'] != 'Completed':
                                    db.update_task_status(row['id'], 'Completed')
                                    st.rerun()
                                elif not is_checked and row['status'] == 'Completed':
                                    db.update_task_status(row['id'], 'Pending')
                                    st.rerun()
                            with col_text:
                                content = f"{icon} {row['task']}{time_str}"
                                if row['status'] == 'Completed':
                                    st.markdown(f"~~{content}~~")
                                else:
                                    st.markdown(content)
                                st.caption(f"{row['due_date']}")
        else:
            st.info("No items found.")

    with tab2:
        st.subheader("⚠️ Approaching Deadlines (Next 7 Days)")
        
        if not tasks.empty:
            today = date.today()
            next_week = today + pd.Timedelta(days=7)
            
            # Filter for tasks due between today and next week, and not completed
            upcoming_tasks = tasks[
                (tasks['due_date_dt'] >= today) & 
                (tasks['due_date_dt'] <= next_week) & 
                (tasks['status'] != 'Completed')
            ].sort_values(by='due_date_dt')
            
            if not upcoming_tasks.empty:
                for index, row in upcoming_tasks.iterrows():
                    days_left = (row['due_date_dt'] - today).days
                    color = "red" if days_left <= 1 else "orange" if days_left <= 3 else "green"
                    
                    with st.container():
                        st.markdown(f"""
                        <div style="padding: 10px; border-left: 5px solid {color}; background-color: #262730; margin-bottom: 10px; border-radius: 5px;">
                            <strong>{row['task']}</strong> <br>
                            <span style="color: #aaa; font-size: 0.8em;">Due: {row['due_date']} ({days_left} days left)</span>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.success("No upcoming deadlines for the next 7 days!")
        else:
            st.info("No tasks found.")

elif page == "Calendar":
    st.title("📅 Calendar")
    
    tasks = db.get_tasks()
    events = []
    for index, row in tasks.iterrows():
        start = row['due_date']
        if row['item_time'] and row['item_time'] != 'None':
            start = f"{row['due_date']}T{row['item_time']}"
        
        events.append({
            "title": row['task'],
            "start": start,
            "backgroundColor": "#ff4b4b" if row['category'] == "🔥 Critical" else "#3788d8",
            "borderColor": "#ff4b4b" if row['category'] == "🔥 Critical" else "#3788d8",
        })

    calendar_options = {
        "headerToolbar": {
            "left": "today prev,next",
            "center": "title",
            "right": "dayGridMonth,timeGridWeek,timeGridDay",
        },
        "initialView": "dayGridMonth",
    }
    
    calendar(events=events, options=calendar_options)

elif page == "Analytics":
    st.title("📊 Analytics")
    
    tasks = db.get_tasks()
    
    if not tasks.empty:
        # Ensure due_date is datetime
        tasks['due_date'] = pd.to_datetime(tasks['due_date'])
        tasks['completed'] = tasks['status'].apply(lambda x: 1 if x == 'Completed' else 0)
        
        # Weekly Progress (Last 7 Days)
        st.subheader("Weekly Progress (Last 7 Days)")
        end_date = pd.Timestamp.now().normalize()
        start_date = end_date - pd.Timedelta(days=6)
        
        weekly_data = tasks[(tasks['due_date'] >= start_date) & (tasks['due_date'] <= end_date)]
        
        if not weekly_data.empty:
            daily_stats = weekly_data.groupby('due_date')['completed'].mean().reset_index()
            daily_stats['completed'] = daily_stats['completed'] * 100
            daily_stats['due_date'] = daily_stats['due_date'].dt.strftime('%Y-%m-%d')
            
            fig_weekly = px.bar(daily_stats, x='due_date', y='completed', 
                                title="Daily Completion Rate (%)",
                                labels={'due_date': 'Date', 'completed': 'Completion (%)'},
                                range_y=[0, 100])
            st.plotly_chart(fig_weekly, use_container_width=True)
        else:
            st.info("No tasks found for the last 7 days.")

        # Monthly Progress (Last 30 Days)
        st.subheader("Monthly Progress (Last 30 Days)")
        start_date_month = end_date - pd.Timedelta(days=29)
        
        monthly_data = tasks[(tasks['due_date'] >= start_date_month) & (tasks['due_date'] <= end_date)]
        
        if not monthly_data.empty:
            daily_stats_month = monthly_data.groupby('due_date')['completed'].mean().reset_index()
            daily_stats_month['completed'] = daily_stats_month['completed'] * 100
            daily_stats_month['due_date'] = daily_stats_month['due_date'].dt.strftime('%Y-%m-%d')
            
            fig_monthly = px.line(daily_stats_month, x='due_date', y='completed', 
                                  title="30-Day Completion Trend",
                                  labels={'due_date': 'Date', 'completed': 'Completion (%)'},
                                  range_y=[0, 100], markers=True)
            st.plotly_chart(fig_monthly, use_container_width=True)
        else:
            st.info("No tasks found for the last 30 days.")
            
        # Category Breakdown
        st.subheader("Task Distribution by Category")
        cat_counts = tasks['category'].value_counts().reset_index()
        cat_counts.columns = ['category', 'count']
        fig_cat = px.pie(cat_counts, values='count', names='category', title="Tasks by Category")
        st.plotly_chart(fig_cat, use_container_width=True)

    else:
        st.info("No tasks available for analytics.")
