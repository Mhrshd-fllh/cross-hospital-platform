"""
Feedback page for the Cross-Hospital Generalization Platform.
Collects and displays physician feedback on model predictions.
"""

import streamlit as st
import pandas as pd
from datetime import datetime

# Import services
from frontend.services.feedback_service import FeedbackService

def create_feedback_service():
    """Create an instance of the feedback service."""
    return FeedbackService()

def get_feedback_status_badge(agreed: bool, ground_truth_available: bool) -> str:
    """Generate HTML for feedback status badge."""
    if agreed:
        return '''
        <span style="
            background-color: #28a745;
            color: white;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 0.8em;
            font-weight: bold;
        ">AGREED</span>
        '''
    else:
        if ground_truth_available:
            return '''
            <span style="
                background-color: #dc3545;
                color: white;
                padding: 2px 8px;
                border-radius: 10px;
                font-size: 0.8em;
                font-weight: bold;
            ">DISAGREED</span>
            '''
        else:
            return '''
            <span style="
                background-color: #ffc107;
                color: #212529;
                padding: 2px 8px;
                border-radius: 10px;
                font-size: 0.8em;
                font-weight: bold;
            ">DISAGREED (NO GT)</span>
            '''

def render_feedback_table(feedback_entries):
    """Render feedback entries as a table"""
    # Convert to DataFrame for display
    df = pd.DataFrame([{
        "ID": fb.feedback_id,
        "Request ID": fb.request_id,
        "Timestamp": fb.timestamp,
        "Hospital": fb.hospital,
        "Prediction": fb.prediction,
        "Physician": fb.physician_name,
        "Agreed": fb.agreed,
        "Confidence": f"{fb.confidence:.1%}",
        "Ground Truth": gt if gt else "-"
    } for fb in feedback_entries])

    # Configure column display
    column_config = {
        "Timestamp": st.column_config.DatetimeColumn(
            "Timestamp",
            format="MM/DD/YYYY HH:mm:ss"
        ),
        "Agreed": st.column_config.CheckboxColumn(
            "Agreed",
            width="small"
        ),
        "Confidence": st.column_config.TextColumn(
            "Confidence",
            width="small"
        )
    }

    # Display the dataframe
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config=column_config,
        on_select="rerun",
        selection_mode="single-row"
    )

def render_feedback_details(feedback):
    """Render detailed view of a selected feedback entry"""
    st.header(f"Feedback Details: {feedback.feedback_id}")

    # Determine status
    agreed = feedback.agreed
    ground_truth_available = bool(feedback.ground_truth)

    # Status badge
    if agreed:
        status_bg = "#d4edda"
        status_text = "AGREED"
        status_color = "#155724"
    else:
        if ground_truth_available:
            status_bg = "#f8d7da"
            status_text = "DISAGREED"
            status_color = "#721c24"
        else:
            status_bg = "#fff3cd"
            status_text = "DISAGREED (NO GT)"
            status_color = "#856404"

    # Feedback header
    st.markdown(f"""
    <div style="
        padding: 1.5rem;
        border-radius: 0.5rem;
        border-left: 4px solid {status_color};
        background-color: {status_bg};
        margin-bottom: 1.5rem;
    ">
        <h2 style="color: {status_color}; margin-top: 0;">
            Physician Feedback
        </h2>
        <p><strong>Status:</strong> <span style="color: {status_color}; font-weight: bold;">{status_text}</span></p>
    </div>
    """, unsafe_allow_html=True)

    # Basic information
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Timestamp", feedback.timestamp.strftime("%Y-%m-%d %H:%M:%S"))
        st.metric("Request ID", feedback.request_id)

    with col2:
        st.metric("Feedback ID", feedback.feedback_id)
        st.metric("Hospital", feedback.hospital)

    with col3:
        st.metric("Physician", feedback.physician_name or "Unknown")
        confidence_pct = f"{feedback.confidence:.1%}"
        st.metric("AI Confidence", confidence_pct)

    st.markdown("---")

    # Prediction comparison
    st.subheader("Prediction Comparison")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### AI Prediction")
        st.markdown(f"# {feedback.prediction}")
        st.caption(f"Confidence: {feedback.confidence:.1%}")

    with col2:
        if agreed:
            st.markdown("### Physician Assessment")
            st.markdown(f"# {feedback.prediction}")
            st.caption("Agrees with AI prediction")
        else:
            if feedback.correct_diagnosis:
                st.markdown("### Physician Assessment")
                st.markdown(f"# {feedback.correct_diagnosis}")
                if feedback.ground_truth:
                    if feedback.ground_truth == feedback.correct_diagnosis:
                        st.caption("Matches ground truth")
                    else:
                        st.caption(f"Differs from ground truth ({feedback.ground_truth})")
                else:
                    st.caption("Ground truth not available")
            else:
                st.markdown("### Physician Assessment")
                st.markdown("# No diagnosis provided")
                st.caption("Feedback indicates disagreement but no alternative diagnosis")

    # Feedback comments
    if feedback.comments:
        st.markdown("---")
        st.subheader("Physician Comments")
        st.info(feedback.comments)

    # Ground truth information
    if ground_truth_available:
        st.markdown("---")
        st.subheader("Ground Truth Information")
        gt_col1, gt_col2 = st.columns(2)
        with gt_col1:
            st.metric("Ground Truth", feedback.ground_truth or "Not available")
        with gt_col2:
            if feedback.ground_truth_available:
                match_ai = feedback.ground_truth == feedback.prediction
                match_phys = feedback.ground_truth == feedback.correct_diagnosis if feedback.correct_diagnosis else False
                st.metric("Matches AI Prediction", "Yes" if match_ai else "No")
                if feedback.correct_diagnosis:
                    st.metric("Matches Physician", "Yes" if match_phys else "No")

    # Additional metadata
    st.markdown("---")
    st.subheader("Additional Metadata")

    meta_col1, meta_col2 = st.columns(2)
    with meta_col1:
        if feedback.physician_id:
            st.text(f"Physician ID: {feedback.physician_id}")
        # Add other metadata as needed

    with meta_col2:
        # This would typically be a link to view the actual image
        if feedback.request_id:
            st.text(f"Associated Request: {feedback.request_id}")

    # Feedback action buttons (for demo purposes)
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button("📋 Feedback Summary", use_container_width=True):
            st.info("Feedback summary report would be generated here")

    with col2:
        if st.button("🔄 Refresh Feedback", use_container_width=True):
            st.info("Refreshing feedback data...")
            # Clear cached data to force reload
            if 'feedback_data' in st.session_state:
                del st.session_state.feedback_data
            if 'selected_feedback' in st.session_state:
                del st.session_state.selected_feedback
            st.experimental_rerun()

    with col3:
        if st.button("← Back to Feedback List", use_container_width=True):
            if 'selected_feedback' in st.session_state:
                del st.session_state.selected_feedback
            st.experimental_rerun()

def feedback_page():
    """Main feedback page function"""
    # Header
    st.header("💬 Physician Feedback")
    st.markdown("Collect and review physician feedback on AI model predictions")

    # Create feedback service
    feedback_service = create_feedback_service()

    # Get request ID from session state (if we're viewing feedback for a specific request)
    # For the feedback page, we typically show a list or a form to submit new feedback
    # Let's check if we have a specific request ID to show feedback for
    if 'feedback_request_id' in st.session_state:
        request_id = st.session_state.feedback_request_id
        st.subheader(f"Feedback for Request: {request_id}")

        # Get feedback for this specific request
        try:
            with st.spinner("Loading feedback for this request..."):
                feedback_list = feedback_service.get_feedback_for_request(request_id)
        except Exception as e:
            st.error(f"Error loading feedback: {str(e)}")
            feedback_list = []

        if feedback_list:
            # Show feedback list for this request
            st.write(f"Found {len(feedback_list)} feedback entries for this request:")
            render_feedback_table(feedback_list)

            # Allow selecting a feedback item to view details
            # Note: Streamlit's selection handling is limited, so we'll use a different approach
            selected_idx = st.selectbox(
                "Select feedback to view details:",
                options=range(len(feedback_list)),
                format_func=lambda i: f"Feedback {feedback_list[i].feedback_id} - {feedback_list[i].physician_name or 'Unknown'} ({feedback_list[i].timestamp.strftime('%m/%d %H:%M')})"
            )

            if st.button("View Feedback Details"):
                st.session_state.selected_feedback = feedback_list[selected_idx]
                st.experimental_rerun()
        else:
            st.info("No feedback has been submitted for this request yet.")

            # Option to submit new feedback
            st.markdown("---")
            st.subheader("Submit Feedback for This Request")

            # Get request details (in a real implementation, we'd fetch this from a service)
            # For demo, we'll use mock data
            request_info = {
                "request_id": request_id,
                "prediction": "Pneumonia",  # Would come from inference service
                "confidence": 0.87,         # Would come from inference service
                "hospital": "General Hospital"  # Would come from request metadata
            }

            st.info(f"**AI Prediction:** {request_info['prediction']} ({request_info['confidence']:.1%} confidence)")
            st.info(f"**Hospital:** {request_info['hospital']}")

            # Feedback form
            with st.form("feedback_form"):
                agreed = st.radio(
                    "Do you agree with the AI's assessment?",
                    options=[True, False],
                    format_func=lambda x: "Yes, I agree" if x else "No, I disagree",
                    horizontal=True
                )

                correct_diagnosis = None
                comments = ""

                if not agreed:
                    correct_diagnosis = st.selectbox(
                        "What is the correct diagnosis?",
                        options=["Normal", "Pneumonia", "Cardiomegaly", "Edema", "Fracture", "Nodule", "Other"],
                        index=1  # Default to Pneumonia (different from AI prediction)
                    )
                    if correct_diagnosis == "Other":
                        custom_diagnosis = st.text_input("Please specify the correct diagnosis:")
                        if custom_diagnosis:
                            correct_diagnosis = custom_diagnelse:
                        comments = st.text_area(
                            "Comments (optional):",
                            placeholder="Please provide any additional observations or concerns..."
                        )

                submitted = st.form_submit_button("Submit Feedback", type="primary")

                if submitted:
                    # In a real implementation, we would call the feedback service
                    # For demo, we'll just show a success message
                    st.success("Feedback submitted successfully!")
                    # Clear the form by rerunning
                    if 'feedback_request_id' in st.session_state:
                        del st.session_state.feedback_request_id
                    st.experimental_rerun()

    else:
        # Show general feedback list and statistics
        st.subheader("Recent Feedback Entries")
        st.markdown("Chronological list of physician feedback on AI predictions")

        # Get feedback data from service
        try:
            with st.spinner("Loading recent feedback..."):
                feedback_list = feedback_service.get_recent_feedback(limit=50)
        except Exception as e:
            st.error(f"Error loading feedback: {str(e)}")
            return

        if not feedback_list:
            st.info("No feedback data available.")
            return

        # Summary metrics
        # Calculate stats from feedback list
        total_feedback = len(feedback_list)
        agreed_count = sum(1 for fb in feedback_list if fb.agreed)
        agreement_rate = agreed_count / total_feedback if total_feedback > 0 else 0
        disagreement_rate = 1 - agreement_rate
        pending_review = sum(1 for fb in feedback_list if not fb.agreed and not bool(getattr(fb, 'ground_truth', '')))

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Feedback", total_feedback)
        with col2:
            st.metric("Agreement Rate", f"{agreement_rate:.1%}")
        with col3:
            st.metric("Disagreement Rate", f"{disagreement_rate:.1%}")
        with col3:
            st.metric("Pending Review", pending_review)

        st.markdown("---")

        # Filters and controls
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            agreement_filter = st.multiselect(
                "Filter by Agreement",
                options=["Agreed", "Disagreed"],
                default=["Agreed", "Disagreed"]
            )

        with col2:
            # In a real implementation, we would get hospitals from the service
            hospital_options = list(set(fb.hospital for fb in feedback_list))
            hospital_filter = st.multiselect(
                "Filter by Hospital",
                options=hospital_options,
                default=hospital_options
            )

        with col3:
            date_range = st.selectbox(
                "Time Range",
                options=["Last 24 Hours", "Last 7 Days", "Last 30 Days", "Custom"],
                index=1  # Default to Last 7 Days
            )

        with col4:
            if st.button("🔄 Refresh", use_container_width=True):
                st.experimental_rerun()

        # Apply filters
        filtered_feedback = feedback_list
        if agreement_filter:
            agreement_bool = [ag == "Agreed" for ag in agreement_filter]
            if len(agreement_bool) == 2:  # Both selected
                pass  # No filtering needed
            elif "Agreed" in agreement_filter:
                filtered_feedback = [fb for fb in filtered_feedback if fb.agreed]
            elif "Disagreed" in agreement_filter:
                filtered_feedback = [fb for fb in filtered_feedback if not fb.agreed]
        if hospital_filter:
            filtered_feedback = [fb for fb in filtered_feedback if fb.hospital in hospital_filter]

        # Date range filtering would require parsing timestamps
        # For simplicity, we're showing all since our mock data is recent

        st.markdown(f"**Showing {len(filtered_feedback)} of {len(feedback_list)} feedback entries**")

        st.markdown("---")

        # Render feedback table
        render_feedback_table(filtered_feedback)

        # TODO comments for future integration
        st.markdown("---")
        st.markdown("### 🔧 Future Integration Points")
        st.markdown("""
        - TODO: Connect to actual FeedbackService (replace mock)
        - TODO: Implement real-time feedback notifications
        - TODO: Add ability to link feedback to specific images in a viewer
        - TODO: Add feedback analytics and trends over time
        - TODO: Add ability to export feedback data for model retraining
        - TODO: Add sentiment analysis on feedback comments
        - TODO: Add ability to tag feedback by radiologist specialty
        - TODO: Add feedback-based alerting for systematic disagreements
        - TODO: Integrate with quality improvement systems
        - TODO: Add ability to request additional information from physicians
        - TODO: Add feedback-based model performance tracking
        """)