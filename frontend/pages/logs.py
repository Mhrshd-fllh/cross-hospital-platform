"""
Logs page for the Cross-Hospital Generalization Platform.
Displays request logs, processing history, and audit trails.
"""

import streamlit as st
import pandas as pd
from datetime import datetime

# Import services
from frontend.services.logging_service import LoggingService

def create_logging_service():
    """Create an instance of the logging service."""
    return LoggingService()

def get_status_badge(status: str) -> str:
    """Generate HTML for status badge."""
    status_lower = status.lower()
    if status_lower == "completed":
        return '''
        <span style="
            background-color: #28a745;
            color: white;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.8em;
            font-weight: bold;
        ">COMPLETED</span>
        '''
    elif status_lower == "processing":
        return '''
        <span style="
            background-color: #ffc107;
            color: #212529;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.8em;
            font-weight: bold;
        ">PROCESSING</span>
        '''
    elif status_lower == "failed":
        return '''
        <span style="
            background-color: #dc3545;
            color: white;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.8em;
            font-weight: bold;
        ">FAILED</span>
        '''
    elif status_lower == "pending":
        return '''
        <span style="
            background-color: #17a2b8;
            color: white;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.8em;
            font-weight: bold;
        ">PENDING</span>
        '''
    else:
        return '''
        <span style="
            background-color: #6c757d;
            color: white;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.8em;
            font-weight: bold;
        ">UNKNOWN</span>
        '''

def render_logs_table(logs):
    """Render logs as a table"""
    # Convert to DataFrame for display
    df = pd.DataFrame([{
        "Timestamp": log.timestamp,
        "Request ID": log.request_id,
        "Hospital": log.hospital,
        "Prediction": log.prediction or "-",
        "Confidence": f"{log.confidence:.1%}" if log.confidence else "-",
        "Latency (ms)": log.latency_ms or 0,
        "Drift Score": f"{log.drift_score:.3f}" if log.drift_score is not None else "-",
        "Model Used": log.model_used or "-",
        "Status": log.status
    } for log in logs])

    # Configure column display
    column_config = {
        "Timestamp": st.column_config.DatetimeColumn(
            "Timestamp",
            format="MM/DD/YYYY HH:mm:ss"
        ),
        "Confidence": st.column_config.TextColumn(
            "Confidence",
            width="small"
        ),
        "Drift Score": st.column_config.TextColumn(
            "Drift Score",
            width="small"
        ),
        "Status": st.column_config.TextColumn(
            "Status",
            width="small"
        )
    }

    # Display the dataframe
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config=column_config
    )

def render_log_details(log):
    """Render detailed view of a log entry"""
    st.header(f"Log Details: {log.request_id}")

    # Status badge
    status_badge_html = get_status_badge(log.status)
    st.markdown(f"""
    <div style="
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid {'#28a745' if log.status == 'completed' else '#ffc107' if log.status == 'processing' else '#dc3545' if log.status == 'failed' else '#17a2b8'};
        margin-bottom: 1.5rem;
    ">
        <h2 style="margin-top: 0;">
            Processing Log
        </h2>
        <p><strong>Status:</strong> {status_badge_html}</p>
    </div>
    """, unsafe_allow_html=True)

    # Basic information
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Timestamp", log.timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        st.metric("Request ID", log.request_id)

    with col2:
        st.metric("Hospital", log.hospital)
        if log.prediction:
            confidence_pct = f"{log.confidence:.1%}" if log.confidence else "N/A"
            st.metric("Prediction", f"{log.prediction} ({confidence_pct})")
        else:
            st.metric("Prediction", "N/A")

    with col3:
        st.metric("Latency", f"{log.latency_ms} ms" if log.latency_ms else "N/A")
        drift_score = f"{log.drift_score:.3f}" if log.drift_score is not None else "N/A"
        st.metric("Drift Score", drift_score)
        st.metric("Model Used", log.model_used or "N/A")

    st.markdown("---")

    # Processing stages timeline
    if log.processing_stages:
        st.subheader("Processing Stages")

        # Calculate total time
        total_time = sum(stage.duration_ms for stage in log.processing_stages if stage.duration_ms)

        cols = st.columns(len(log.processing_stages))
        for i, (col, stage) in enumerate(zip(cols, log.processing_stages)):
            with col:
                status_color = "#28a745" if stage.status == "completed" else "#ffc107" if stage.status == "processing" else "#dc3545" if stage.status == "failed" else "#6c757d"
                status_icon = "✅" if stage.status == "completed" else "🔄" if stage.status == "processing" else "❌" if stage.status == "failed" else "⏳"

                st.markdown(f"""
                <div style="text-align: center; padding: 0.5rem;">
                    <div style="font-size: 1.2rem; color: {status_color};">{status_icon}</div>
                    <div style="font-size: 0.9rem; font-weight: bold; color: {status_color};">{stage.name}</div>
                    <div style="font-size: 0.8rem; color: {status_color};">{stage.duration_ms}ms</div>
                </div>
                """, unsafe_allow_html=True)

                # Expandable details for each stage
                with st.expander(f"Details: {stage.name}"):
                    if stage.status == "failed":
                        st.error("This stage failed during processing")
                    elif stage.status == "skipped":
                        st.info("This stage was skipped based on previous results")
                    elif stage.status == "completed":
                        st.success("This stage completed successfully")
                    else:
                        st.info("This stage is currently processing")

    st.markdown("<br>", unsafe_allow_html=True)

    # Metadata
    if log.metadata:
        st.subheader("Request Metadata")

        meta_col1, meta_col2 = st.columns(2)

        with meta_col1:
            st.text(f"Patient ID: {log.metadata.get('patient_id', 'N/A')}")
            st.text(f"Study Date: {log.metadata.get('study_date', 'N/A')}")
            st.text(f"Modality: {log.metadata.get('modality', 'N/A')}")
            st.text(f"Body Part: {log.metadata.get('body_part', 'N/A')}")

        with meta_col2:
            st.text(f"Image Size: {log.metadata.get('image_size', 'N/A')}")
            st.text(f"Image Format: {log.metadata.get('image_format', 'N/A')}")

    st.markdown("<br>", unsafe_allow_html=True)

    # Errors (if any)
    if log.errors:
        st.subheader("Errors Encountered")
        for error in log.errors:
            st.error(f"**{error.stage}**: {error.message} (Code: {error.error_code})")
    else:
        st.success("No errors encountered during processing")

    st.markdown("<br>", unsafe_allow_html=True)

    # Action buttons
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button("📥 Download Log Details", use_container_width=True):
            st.info("Log download functionality would be implemented here")

    with col2:
        if st.button("🔄 Refresh Logs", use_container_width=True):
            st.info("Refreshing logs...")
            # Clear cached data to force reload
            if 'logs_data' in st.session_state:
                del st.session_state.logs_data
            st.experimental_rerun()

    with col3:
        if st.button("← Back to Logs List", use_container_width=True):
            if 'selected_log' in st.session_state:
                del st.session_state.selected_log
            st.experimental_rerun()

def logs_page():
    """Main logs page function"""
    # Header
    st.header("📋 Request Logs")
    st.markdown("View and analyze processing logs for all requests through the CHGP platform")

    # Create logging service
    logging_service = create_logging_service()

    # Check if we're viewing a specific log or the list
    if 'selected_log' in st.session_state:
        # Show detailed view of selected log
        log = st.session_state.selected_log
        render_log_details(log)

        if st.button("← Back to Logs List"):
            del st.session_state.selected_log
            st.experimental_rerun()
    else:
        # Show logs list
        st.subheader("Recent Processing Logs")
        st.markdown("Chronological list of all requests processed through the system")

        # Get logs data from service
        try:
            with st.spinner("Loading logs..."):
                logs = logging_service.get_logs(limit=100)  # Get recent logs
        except Exception as e:
            st.error(f"Error loading logs: {str(e)}")
            return

        if not logs:
            st.info("No log data available.")
            return

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Logs", len(logs))
        with col2:
            completed_count = sum(1 for log in logs if log.status == "completed")
            st.metric("Successful", completed_count)
        with col3:
            failed_count = sum(1 for log in logs if log.status == "failed")
            st.metric("Failed", failed_count)
        with col4:
            processing_count = sum(1 for log in logs if log.status in ["processing", "pending"])
            st.metric("In Progress", processing_count)

        st.markdown("---")

        # Filters and controls
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            status_filter = st.multiselect(
                "Filter by Status",
                options=["completed", "processing", "failed", "pending"],
                default=["completed", "processing", "failed", "pending"]
            )

        with col2:
            # Get unique hospitals from logs
            hospitals = list(set(log.hospital for log in logs if log.hospital))
            hospital_filter = st.multiselect(
                "Filter by Hospital",
                options=hospitals,
                default=hospitals
            )

        with col3:
            date_range = st.selectbox(
                "Time Range",
                options=["Last Hour", "Last 6 Hours", "Last 24 Hours", "Last 7 Days", "Custom"],
                index=2  # Default to Last 24 Hours
            )

        with col4:
            if st.button("🔄 Refresh", use_container_width=True):
                # In a real implementation, this would fetch fresh data
                st.experimental_rerun()

        # Apply filters (simplified - in reality, filtering would be done server-side)
        filtered_logs = logs
        if status_filter:
            filtered_logs = [log for log in filtered_logs if log.status in status_filter]
        if hospital_filter:
            filtered_logs = [log for log in filtered_logs if log.hospital in hospital_filter]

        # Date range filtering would require more complex logic
        # For simplicity, we're showing all since our mock data is already time-limited

        st.markdown(f"**Showing {len(filtered_logs)} of {len(logs)} log entries**")

        st.markdown("---")

        # Render logs table
        render_logs_table(filtered_logs)

        # TODO comments for future integration
        st.markdown("---")
        st.markdown("### 🔧 Future Integration Points")
        st.markdown("""
        - TODO: Connect to actual LoggingService (replace mock)
        - TODO: Integrate with actual logging system (ELK stack, Splunk, etc.)
        - TODO: Implement real-time log streaming (WebSocket or Server-Sent Events)
        - TODO: Add advanced filtering (by date range, error codes, processing stages)
        - TODO: Add search functionality (search by request ID, patient ID, etc.)
        - TODO: Add log export capabilities (CSV, JSON, PDF)
        - TODO: Add log-level filtering (DEBUG, INFO, WARN, ERROR)
        - TODO: Add correlation ID tracking for distributed tracing
        - TODO: Link to specific error traces and stack traces
        - TODO: Add ability to replay failed requests (with appropriate safeguards)
        - TODO: Add performance metrics and bottleneck analysis
        """)