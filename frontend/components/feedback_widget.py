"""
Feedback widget component for the Cross-Hospital Generalization Platform.
Provides reusable components for collecting and displaying user feedback.
"""

import streamlit as st
from datetime import datetime

def render_feedback_widget(title="Feedback", feedback_type="rating",
                         placeholder="Share your thoughts...", key=None):
    """
    Render a generic feedback widget.

    Args:
        title (str): Title of the feedback section
        feedback_type (str): Type of feedback ('rating', 'thumbs', 'stars', 'text', 'emoji')
        placeholder (str): Placeholder text for text input
        key (str, optional): Unique key for the widget

    Returns:
        dict: Feedback data based on type
    """
    st.subheader(title)

    feedback_data = {}

    if feedback_type == "rating":
        # Numerical rating (e.g., 1-5 or 1-10)
        rating = st.slider("Rating", 1, 5, 3, key=f"{key}_rating" if key else None)
        feedback_data["rating"] = rating
        feedback_data["type"] = "rating"

    elif feedback_type == "thumbs":
        # Thumbs up/down
        col1, col2 = st.columns(2)
        with col1:
            if st.button("👍 Thumbs Up", key=f"{key}_thumb_up" if key else None):
                feedback_data["thumb"] = "up"
        with col2:
            if st.button("👎 Thumbs Down", key=f"{key}_thumb_down" if key else None):
                feedback_data["thumb"] = "down"

        if "thumb" in feedback_data:
            feedback_data["type"] = "thumbs"

    elif feedback_type == "stars":
        # Star rating (using slider as proxy)
        stars = st.slider("Rating", 1, 5, 3, key=f"{key}_stars" if key else None)
        feedback_data["stars"] = stars
        feedback_data["type"] = "stars"

    elif feedback_type == "emoji":
        # Emoji feedback
        emojis = ["😞", "😕", "😐", "🙂", "😊"]
        cols = st.columns(len(emojis))
        for i, emoji in enumerate(emojis):
            with cols[i]:
                if st.button(emoji, key=f"{key}_emoji_{i}" if key else None):
                    feedback_data["emoji"] = emoji
                    feedback_data["rating"] = i + 1  # Convert to numeric score
                    feedback_data["type"] = "emoji"

    elif feedback_type == "text":
        # Text feedback
        text = st.text_area(
            "Your Feedback",
            placeholder=placeholder,
            height=100,
            key=f"{key}_text" if key else None
        )
        if text:
            feedback_data["text"] = text
            feedback_data["type"] = "text"

    elif feedback_type == "detailed":
        # Detailed feedback with multiple fields
        col1, col2 = st.columns(2)
        with col1:
            rating = st.slider("Overall Rating", 1, 5, 3, key=f"{key}_rating" if key else None)
            feedback_data["rating"] = rating
        with col2:
            recommend = st.selectbox(
                "Would you recommend this?",
                ["Yes", "Maybe", "No"],
                index=1,
                key=f"{key}_recommend" if key else None
            )
            feedback_data["recommend"] = recommend

        # Additional comments
        comments = st.text_area(
            "Additional Comments",
            placeholder="Please share any additional thoughts or suggestions...",
            height=100,
            key=f"{key}_comments" if key else None
        )
        if comments:
            feedback_data["comments"] = comments

        feedback_data["type"] = "detailed"

    # Add timestamp
    feedback_data["timestamp"] = datetime.now().isoformat()

    # Add any additional context that might be passed in
    if hasattr(st.session_state, 'current_context'):
        feedback_data["context"] = st.session_state.current_context

    return feedback_data if feedback_data else None

def render_medical_feedback_form():
    """
    Render a specialized feedback form for medical image analysis.

    Returns:
        dict: Feedback data specific to medical imaging context
    """
    st.subheader("Clinical Feedback on AI Prediction")

    # Initialize feedback data
    feedback = {
        "timestamp": datetime.now().isoformat(),
        "feedback_type": "medical_imaging"
    }

    # Agreement with AI prediction
    st.write("**Do you agree with the AI's assessment?**")
    agreement = st.radio(
        "Agreement",
        ["Strongly Agree", "Agree", "Unsure", "Disagree", "Strongly Disagree"],
        horizontal=True,
        label_visibility="collapsed"
    )
    feedback["agreement"] = agreement

    # If not fully in agreement, ask for correct assessment
    if agreement in ["Disagree", "Strongly Disagree", "Unsure"]:
        st.write("**What is your assessment?**")
        correct_assessment = st.text_input(
            "Your diagnosis/assessment:",
            placeholder="Enter your clinical assessment...",
            label_visibility="collapsed"
        )
        if correct_assessment:
            feedback["correct_assessment"] = correct_assessment

        # Confidence in your assessment
        confidence = st.slider(
            "Confidence in your assessment:",
            1, 5, 3,
            help="1 = Not confident, 5 = Completely confident"
        )
        feedback["confidence"] = confidence

    # Specific feedback on the AI prediction
    st.write("**Feedback on AI Prediction:**")
    feedback_aspects = st.multiselect(
        "What aspects would you like to comment on?",
        ["Accuracy", "Relevance", "Clinical usefulness", "False positive concern",
         "False negative concern", "Uncertainty estimation", "Other"],
        label_visibility="collapsed"
    )
    feedback["feedback_aspects"] = feedback_aspects

    # Detailed comments
    comments = st.text_area(
        "Detailed Comments:",
        placeholder="Please provide any additional feedback about the AI's performance, "
                   "what was helpful, what could be improved, etc.",
        height=150,
        label_visibility="collapsed"
    )
    if comments:
        feedback["comments"] = comments

    # Would you like to provide the ground truth?
    provide_gt = st.checkbox(
        "I can provide the ground truth/diagnosis for this case",
        value=False
    )
    if provide_gt:
        ground_truth = st.text_input(
            "Ground Truth Diagnosis:",
            placeholder="What is the confirmed diagnosis?",
            label_visibility="collapsed"
        )
        if ground_truth:
            feedback["ground_truth"] = ground_truth

    # Optional: Contact information for follow-up
    follow_up = st.checkbox("May we contact you for follow-up questions?", value=False)
    if follow_up:
        contact_info = st.text_input(
            "Contact Information (email or ID):",
            placeholder="Optional: Provide contact for follow-up",
            label_visibility="collapsed"
        )
        if contact_info:
            feedback["contact_info"] = contact_info

    return feedback

def render_feedback_history(feedback_list, max_items=10):
    """
    Render a history of feedback submissions.

    Args:
        feedback_list (list): List of feedback dictionaries
        max_items (int): Maximum number of items to display
    """
    if not feedback_list:
        st.info("No feedback history available")
        return

    st.subheader("Recent Feedback")

    # Limit to most recent items
    recent_feedback = feedback_list[-max_items:] if len(feedback_list) > max_items else feedback_list
    recent_feedback.reverse()  # Show newest first

    for i, feedback in enumerate(recent_feedback):
        with st.expander(f"Feedback #{len(feedback_list)-i} - {feedback.get('timestamp', 'Unknown time')[:16]}"):
            # Display feedback based on type
            if feedback.get("feedback_type") == "medical_imaging":
                render_medical_feedback_display(feedback)
            else:
                # Generic display
                for key, value in feedback.items():
                    if key not in ["timestamp"]:  # Skip timestamp in detailed view
                        st.text(f"{key.replace('_', ' ').title()}: {value}")

def render_medical_feedback_display(feedback):
    """
    Display medical feedback in a formatted way.

    Args:
        feedback (dict): Feedback dictionary from medical feedback form
    """
    # Agreement status
    agreement = feedback.get("agreement", "Not specified")
    agreement_colors = {
        "Strongly Agree": "green",
        "Agree": "lightgreen",
        "Unsure": "orange",
        "Disagree": "red",
        "Strongly Disagree": "darkred"
    }
    color = agreement_colors.get(agreement, "gray")

    st.markdown(f"""
    <div style="
        background-color: {color}15;
        border-left: 4px solid {color};
        padding: 1rem;
        border-radius: 0.25rem;
        margin-bottom: 1rem;
    ">
        <strong>Agreement with AI:</strong> <span style="color: {color};">{agreement}</span>
    </div>
    """, unsafe_allow_html=True)

    # Other fields
    if "correct_assessment" in feedback:
        st.write(f"**Your Assessment:** {feedback['correct_assessment']}")

    if "confidence" in feedback:
        st.write(f"**Confidence in Your Assessment:** {feedback['confidence']}/5")

    if "feedback_aspects" in feedback and feedback["feedback_aspects"]:
        st.write(f"**Feedback On:** {', '.join(feedback['feedback_aspects'])}")

    if "comments" in feedback and feedback["comments"]:
        st.write(f"**Comments:** {feedback['comments']}")

    if "ground_truth" in feedback and feedback["ground_truth"]:
        st.write(f"**Ground Truth:** {feedback['ground_truth']}")

    if "contact_info" in feedback and feedback["contact_info"]:
        st.write(f"**Contact Info:** {feedback['contact_info']}")

def render_quick_feedback_buttons(positive_text="Helpful", negative_text="Not Helpful",
                                key_prefix=None):
    """
    Render quick feedback buttons for simple positive/negative feedback.

    Args:
        positive_text (str): Text for positive button
        negative_text (str): Text for negative button
        key_prefix (str, optional): Prefix for widget keys

    Returns:
        str: "positive", "negative", or None if no selection made
    """
    col1, col2 = st.columns(2)

    with col1:
        if st.button(f"👍 {positive_text}",
                   key=f"{key_prefix}_positive" if key_prefix else None,
                   use_container_width=True):
            return "positive"

    with col2:
        if st.button(f"👎 {negative_text}",
                   key=f"{key_prefix}_negative" if key_prefix else None,
                   use_container_width=True):
            return "negative"

    return None

def render_feedback_modal_trigger(button_text="Provide Feedback",
                                key=None):
    """
    Render a button that could trigger a feedback modal (placeholder for future implementation).

    Args:
        button_text (str): Text for the button
        key (str, optional): Unique key for the button

    Returns:
        bool: True if button was clicked
    """
    # In a full implementation, this would open a modal/dialog
    # For now, it's just a button that returns True when clicked
    if st.button(button_text, key=key):
        return True
    return False

def export_feedback_to_csv(feedback_list, filename="feedback_export.csv"):
    """
    Export feedback list to CSV format (returns CSV string).

    Args:
        feedback_list (list): List of feedback dictionaries
        filename (str): Name for the file

    Returns:
        str: CSV formatted string
    """
    if not feedback_list:
        return ""

    # Convert to DataFrame and then to CSV
    import pandas as pd
    df = pd.DataFrame(feedback_list)
    return df.to_csv(index=False)