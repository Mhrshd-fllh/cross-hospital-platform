"""
Alerts widget component for the Cross-Hospital Generalization Platform.
Provides reusable components for displaying and managing alerts/notifications.
"""

import streamlit as st
from datetime import datetime, timedelta

def render_alerts_widget(alerts=None, max_visible=5, show_details=False,
                        filter_unread_only=False, key_prefix=None):
    """
    Render a widgets displaying alerts/notifications.

    Args:
        alerts (list): List of alert dictionaries
        max_visible (int): Maximum number of alerts to show
        show_details (bool): Whether to show full alert details
        filter_unread_only (bool): Whether to show only unread/unacknowledged alerts
        key_prefix (str): Prefix for widget keys to avoid conflicts

    Returns:
        dict: Action taken (if any) or None
    """
    if alerts is None:
        alerts = []

    # Filter alerts if requested
    if filter_unread_only:
        alerts = [alert for alert in alerts if not alert.get('acknowledged', False)]

    # Sort by timestamp (newest first) and limit
    sorted_alerts = sorted(alerts, key=lambda x: x.get('timestamp', ''), reverse=True)
    visible_alerts = sorted_alerts[:max_visible]

    if not visible_alerts:
        if filter_unread_only:
            st.info("No unread alerts")
        else:
            st.info("No alerts to display")
        return None

    st.subheader("Recent Alerts")

    action_taken = None

    for i, alert in enumerate(visible_alerts):
        # Determine alert styling based on severity
        severity = alert.get('severity', 'info').lower()
        severity_colors = {
            'critical': {'bg': '#ffebee', 'border': '#f44336', 'icon': '🚨'},
            'error': {'bg': '#ffebee', 'border': '#f44336', 'icon': '❌'},
            'warning': {'bg': '#fff8e1', 'border': '#ff9800', 'icon': '⚠️'},
            'info': {'bg': '#e3f2fd', 'border': '#2196f3', 'icon': 'ℹ️'},
            'success': {'bg': '#e8f5e9', 'border': '#4caf50', 'icon': '✅'}
        }
        style = severity_colors.get(severity, severity_colors['info'])

        # Create a unique key for this alert
        alert_id = alert.get('id', f'alert_{i}')
        alert_key = f"{key_prefix}_{alert_id}" if key_prefix else alert_id

        with st.container():
            # Alert header with icon and timestamp
            col1, col2, col3 = st.columns([1, 8, 1])
            with col1:
                st.markdown(f"<div style='text-align: center;'>{style['icon']}</div>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div style="
                    background-color: {style['bg']};
                    border-left: 4px solid {style['border']};
                    padding: 0.75rem;
                    border-radius: 0.25rem;
                    margin-bottom: 0.5rem;
                ">
                    <strong>{alert.get('type', 'Alert')}</strong><br>
                    <span style="font-size: 0.875rem;">
                        {alert.get('message', 'No message')}
                    </span>
                </div>
                """, unsafe_allow_html=True)
            with col3:
                # Time badge
                time_str = alert.get('timestamp', '')
                if time_str:
                    try:
                        # Try to parse and format time
                        dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                        time_diff = datetime.now() - dt
                        if time_diff.total_seconds() < 3600:  # Less than an hour
                            time_display = f"{int(time_diff.total_seconds() // 60)}m ago"
                        elif time_diff.total_seconds() < 86400:  # Less than a day
                            time_display = f"{int(time_diff.total_seconds() // 3600)}h ago"
                        else:
                            time_display = dt.strftime("%m/%d %H:%M")
                    except:
                        time_display = time_str[:10] if len(time_str) > 10 else time_str
                else:
                    time_display = "Unknown"

                st.markdown(f"""
                <div style="
                    background-color: {style['border']};
                    color: white;
                    padding: 0.25rem 0.5rem;
                    border-radius: 0.25rem;
                    font-size: 0.75rem;
                    text-align: center;
                ">
                    {time_display}
                </div>
                """, unsafe_allow_html=True)

            # Show details if requested
            if show_details:
                with st.expander("Details", expanded=False):
                    # Show additional fields
                    details_to_show = {k: v for k, v in alert.items()
                                     if k not in ['id', 'type', 'message', 'severity', 'timestamp']}
                    for key, value in details_to_show.items():
                        if value is not None and value != "":
                            st.text(f"{key.replace('_', ' ').title()}: {value}")

            # Action buttons for interactive alerts
            if not show_details:  # Only show actions in compact view
                col1, col2, col3 = st.columns([1, 1, 8])
                with col1:
                    if not alert.get('acknowledged', False):
                        if st.button("✓ Ack", key=f"{alert_key}_ack", help="Acknowledge alert"):
                            action_taken = {"action": "acknowledge", "alert_id": alert_id}
                    else:
                        if st.button("↩ Unack", key=f"{alert_key}_unack", help="Unacknowledge alert"):
                            action_taken = {"action": "unacknowledge", "alert_id": alert_id}

                with col2:
                    if not alert.get('resolved', False):
                        if st.button("✓ Res", key=f"{alert_key}_res", help="Resolve alert"):
                            action_taken = {"action": "resolve", "alert_id": alert_id}
                    else:
                        if st.button("↩ Reopen", key=f"{alert_key}_reopen", help="Reopen alert"):
                            action_taken = {"action": "reopen", "alert_id": alert_id}

            # Add some spacing between alerts
            if i < len(visible_alerts) - 1:
                st.markdown("<br>", unsafe_allow_html=True)

    # Show count of hidden alerts if applicable
    if len(sorted_alerts) > max_visible:
        hidden_count = len(sorted_alerts) - max_visible
        if filter_unread_only:
            st.caption(f"+ {hidden_count} more unread alerts")
        else:
            st.caption(f"+ {hidden_count} more alerts")

    return action_taken

def render_alert_badge(count, label="Alerts", prefix="", color=None):
    """
    Render a badge showing alert count.

    Args:
        count (int): Number of alerts
        label (str): Label to display with the count
        prefix (str): Optional prefix (e.g., emoji)
        color (str, optional): Background color (defaults to red if count>0, gray otherwise)
    """
    if count <= 0:
        # Don't show badge if no alerts
        return

    # Determine color
    if color is None:
        color = "red" if count > 0 else "gray"

    # Escape HTML if needed
    safe_label = str(label).replace("&", "&").replace("<", "<").replace(">", ">")

    st.markdown(f"""
    <span style="
        background-color: {color};
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.75rem;
        font-weight: 600;
        vertical-align: middle;
        margin-left: 0.25rem;
    ">
        {prefix}{count} {safe_label}
    </span>
    """, unsafe_allow_html=True)

def render_alert_dropdown(alerts, max_items=5, key=None):
    """
    Render a dropdown menu for alerts (similar to notification bell).

    Args:
        alerts (list): List of alert dictionaries
        max_items (int): Maximum items to show in dropdown
        key (str, optional): Key for the widget

    Returns:
        dict: Selected action or None
    """
    if not alerts:
        # Show empty state
        st.button("🔔 No Alerts", disabled=True, key=f"{key}_empty" if key else None)
        return None

    # Sort by timestamp (newest first)
    sorted_alerts = sorted(alerts, key=lambda x: x.get('timestamp', ''), reverse=True)
    display_alerts = sorted_alerts[:max_items]

    # Create a selectbox with alert summaries
    alert_options = []
    for alert in display_alerts:
        severity_icon = {
            'critical': '🚨',
            'error': '❌',
            'warning': '⚠️',
            'info': 'ℹ️',
            'success': '✅'
        }.get(alert.get('severity', 'info').lower(), '🔔')

        time_str = alert.get('timestamp', '')
        if time_str:
            try:
                dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                time_diff = datetime.now() - dt
                if time_diff.total_seconds() < 3600:
                    time_display = f"{int(time_diff.total_seconds() // 60)}m"
                elif time_diff.total_seconds() < 86400:
                    time_display = f"{int(time_diff.total_seconds() // 3600)}h"
                else:
                    time_display = dt.strftime("%m/%d")
            except:
                time_display = "?"
        else:
            time_display = "?"

        # Create option string
        option_text = f"{severity_icon} {alert.get('type', 'Alert')} ({time_display})"
        alert_options.append((option_text, alert))

    # Add a "View All" option if there are more alerts
    if len(alerts) > max_items:
        alert_options.append(("📋 View All Alerts...", None))

    # The selectbox
    selected_option = st.selectbox(
        "Alerts",
        options=[opt[0] for opt in alert_options],
        index=0,
        label_visibility="collapsed",
        key=f"{key}_dropdown" if key else None
    )

    # Find the selected alert
    selected_alert = None
    for option_text, alert in alert_options:
        if option_text == selected_option:
            selected_alert = alert
            break

    # Handle selection
    if selected_alert is not None and selected_alert != "View All Alerts...":
        # Show alert details in expandable section
        with st.expander(f"Alert Details", expanded=True):
            st.write(f"**Type:** {selected_alert.get('type', 'Unknown')}")
            st.write(f"**Message:** {selected_alert.get('message', 'No message')}")
            st.write(f"**Time:** {selected_alert.get('timestamp', 'Unknown')}")
            st.write(f"**Severity:** {selected_alert.get('severity', 'Unknown').title()}")

            # Action buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if not selected_alert.get('acknowledged', False):
                    if st.button("Acknowledge", key=f"{key}_ack" if key else None):
                        return {"action": "acknowledge", "alert_id": selected_alert.get('id')}
                else:
                    if st.button("Unacknowledge", key=f"{key}_unack" if key else None):
                        return {"action": "unacknowledge", "alert_id": selected_alert.get('id')}

            with col2:
                if not selected_alert.get('resolved', False):
                    if st.button("Resolve", key=f"{key}_res" if key else None):
                        return {"action": "resolve", "alert_id": selected_alert.get('id')}
                else:
                    if st.button("Reopen", key=f"{key}_reopen" if key else None):
                        return {"action": "reopen", "alert_id": selected_alert.get('id')}

            with col3:
                if st.button("Close", key=f"{key}_close" if key else None):
                    return {"action": "dismiss"}

    elif selected_alert == "View All Alerts...":
        return {"action": "view_all"}

    return None

def render_alert_summary_stats(alerts):
    """
    Render summary statistics for alerts.

    Args:
        alerts (list): List of alert dictionaries
    """
    if not alerts:
        st.info("No alerts data available")
        return

    # Calculate stats
    total = len(alerts)
    unacknowledged = sum(1 for a in alerts if not a.get('acknowledged', False))
    unresolved = sum(1 for a in alerts if not a.get('resolved', False))
    critical = sum(1 for a in alerts if a.get('severity', '').lower() == 'critical')
    warnings = sum(1 for a in alerts if a.get('severity', '').lower() == 'warning')

    # Create metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Alerts", total)
    with col2:
        delta_unack = f"-{unacknowledged}" if unacknowledged < total else f"+{unacknowledged}"
        st.metric("Unacknowledged", unacknowledged, delta=delta_unack if unacknowledged > 0 else None)
    with col3:
        delta_unres = f"-{unresolved}" if unresolved < total else f"+{unresolved}"
        st.metric("Unresolved", unresolved, delta=delta_unres if unresolved > 0 else None)
    with col4:
        st.metric("Critical", critical)

def render_alert_feed(alerts, height=300, key=None):
    """
    Render a scrolling feed of alerts.

    Args:
        alerts (list): List of alert dictionaries
        height (int): Height of the feed area in pixels
        key (str, optional): Key for the container

    Returns:
        dict: Action taken or None
    """
    if not alerts:
        st.info("No alerts in feed")
        return None

    # Sort by timestamp (newest first)
    sorted_alerts = sorted(alerts, key=lambda x: x.get('timestamp', ''), reverse=True)

    # Create a container with fixed height
    with st.container():
        # Use markdown to create a scrollable area
        st.markdown(f"""
        <div style="height: {height}px; overflow-y: auto; border: 1px solid #eee; border-radius: 0.25rem; padding: 1rem;">
        """, unsafe_allow_html=True)

        action_taken = None

        for alert in sorted_alerts:
            # Determine styling
            severity = alert.get('severity', 'info').lower()
            severity_colors = {
                'critical': '#ffebee',
                'error': '#ffebee',
                'warning': '#fff8e1',
                'info': '#e3f2fd',
                'success': '#e8f5e9'
            }
            bg_color = severity_colors.get(severity, '#e3f2fd')
            border_color = severity_colors.get(severity, '#2196f3').replace('ef', 'f3').replace('e1', 'f8').replace('e9', 'e5')

            # Time ago calculation
            time_str = alert.get('timestamp', '')
            time_ago = "Unknown"
            if time_str:
                try:
                    dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                    diff = datetime.now() - dt
                    if diff.total_seconds() < 60:
                        time_ago = "just now"
                    elif diff.total_seconds() < 3600:
                        time_ago = f"{int(diff.total_seconds() // 60)}m"
                    elif diff.total_seconds() < 86400:
                        time_ago = f"{int(diff.total_seconds() // 3600)}h"
                    else:
                        time_ago = f"{int(diff.total_seconds() // 86400)}d"
                except:
                    pass

            # Alert item
            st.markdown(f"""
            <div style="
                background-color: {bg_color};
                border-left: 3px solid {border_color};
                padding: 0.75rem;
                margin-bottom: 0.5rem;
                border-radius: 0 0.25rem 0.25rem 0;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>{alert.get('type', 'Alert')}</strong><br>
                        <span style="font-size: 0.875rem; color: #555;">
                            {alert.get('message', 'No message')}
                        </span>
                    </div>
                    <div style="text-align: right; font-size: 0.75rem; color: #666;">
                        {time_ago}<br>
                        <span style="
                            background-color: {border_color};
                            color: white;
                            padding: 0.125rem 0.375rem;
                            border-radius: 0.25rem;
                        ">
                            {severity.upper()}
                        </span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # Close the container div
        st.markdown("</div>", unsafe_allow_html=True)

    return action_taken