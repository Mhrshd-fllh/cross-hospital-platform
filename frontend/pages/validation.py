"""
Validation page for the Cross-Hospital Generalization Platform.
Displays validation results for uploaded medical images using Great Expectations.
"""

import streamlit as st
import pandas as pd
from datetime import datetime

# Import services
from frontend.services.validation_service import ValidationService

def create_validation_service():
    """Create an instance of the validation service."""
    return ValidationService()

def render_validation_check(check):
    """Render a single validation check"""
    # Determine icon and color based on pass/fail status
    if check["pass"]:
        icon = "✅"
        status = "PASS"
    else:
        icon = "❌"
        status = "FAIL"

    # Determine severity color
    severity_colors = {
        "error": "red",
        "warning": "orange",
        "info": "blue"
    }
    color = severity_colors.get(check["severity"], "gray")

    # Create the check item
    with st.container():
        col1, col2, col3 = st.columns([1, 3, 2])

        with col1:
            st.markdown(f"<div style='text-align: center;'>{icon}</div>", unsafe_allow_html=True)

        with col2:
            st.markdown(f"**{check['check']}**")
            st.caption(check["description"])

        with col3:
            if check["pass"]:
                st.markdown(f"<span style='color: green; font-weight: bold;'>{status}</span>", unsafe_allow_html=True}")
            else:
                # Color based on severity
                color = "red" if check["severity"] == "error" else "orange"
                st.markdown(f"Details: {check['check']}"):
                    st.write(check["details"])
                    if not check["pass"] and check["severity"] == "error":
                        st.error("This is a critical validation failure that will block processing.")
                    elif not check["pass"] and check["severity"] == "warning":
                        st.warning("This is a warning that may affect processing quality.")

        st.markdown("---")

def render_validation_summary(validation_result):
    """Render validation summary"""
    overall_status = "PASS" if validation_result.passed else "FAIL"

    # Determine status styling
    if overall_status == "PASS":
        status_color = "green"
        status_icon = "✅"
        status_text = "VALIDATION PASSED"
    else:
        status_color = "red"
        status_icon = "❌"
        status_text = "VALIDATION FAILED"

    # Display summary
    st.markdown(f"""
    <div style="
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid {status_color};
        background-color: rgba({int(status_color.replace('#', ''), 16) if len(status_color) == 7 else 255},
                               {int(status_color[1:3], 16) if len(status_color) == 7 else 255},
                               {int(status_color[3:5], 16) if len(status_color) == 7 else 255}, 0.1);
        margin: 1rem 0;
    ">
        <h3>{status_icon} {status_text}</h3>
        <p><strong>Request ID:</strong> {validation_result.request_id}</p>
        <p><strong>Timestamp:</strong> {validation_result.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Overall Status:</strong> <span style='color: {status_color}; font-weight: bold;'>{overall_status}</span></p>
    </div>
    """, unsafe_allow_html=True)

def render_expanded_report(validation_result):
    """Render expandable validation report"""
    with st.expander("📋 View Detailed Validation Report", expanded=False):
        st.subheader("Validation Report Details")

        # Request information
        st.json({
            "request_id": validation_result.request_id,
            "timestamp": validation_result.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            "validated_by": "CHGP Validation Service v1.0",
            "schema_version": "1.0.0"
        })

        # Summary statistics
        checks = validation_result.checks
        passed = sum(1 for check in checks if check.passed)
        failed = len(checks) - passed
        warnings = sum(1 for check in checks if not check.passed and check.severity == "warning")
        errors = sum(1 for check in checks if not check.passed and check.severity == "error")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Checks", len(checks))
        with col2:
            st.metric("Passed", passed)
        with col3:
            st.metric("Warnings", warnings)
        with col4:
            st.metric("Errors", errors)

        # Detailed results table
        st.subheader("Detailed Results")
        df_data = []
        for check in checks:
            df_data.append({
                "Check": check.check,
                "Status": "PASS" if check.passed else "FAIL",
                "Severity": check.severity.upper(),
                "Description": check.description,
                "Details": check.details
            })

        df = pd.DataFrame(df_data)
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Status": st.column_config.TextColumn(
                    "Status",
                    help": Validation pass/fail status"
                ),
                "Severity": st.column_config.TextColumn(
                    "Severity",
                    help": Issue severity level"
                )
            }
        )

def validation_page():
    """Main validation page function"""
    # Header
    st.header("🔍 Validation Results")
    st.markdown("Review the validation results for the uploaded medical image")

    # Get request ID from session state (should be set from upload page)
    if 'current_request_id' not in st.session_state:
        st.warning("No request ID found. Please upload an image first.")
        if st.button("Go to Upload Page"):
            st.switch_page("upload.py")
        return

    request_id = st.session_state.current_request_id

    # Create validation service
    validation_service = create_validation_service()

    # Get validation results from service
    try:
        with st.spinner("Running validation checks..."):
            validation_result = validation_service.validate_image(request_id)
    except Exception as e:
        st.error(f"Error running validation: {str(e)}")
        return

    # Display validation summary
    render_validation_summary(validation_result)

    # Display individual checks
    st.subheader("Validation Checks")
    st.markdown("Each check below verifies a specific aspect of the image and metadata:")

    for check in validation_result.checks:
        render_validation_check(check)

    # Display expandable report
    render_expanded_report(validation_result)

    # Action buttons
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button("🔄 Re-run Validation", use_container_width=True):
            # Re-run validation
            validation_result = validation_service.validate_image(request_id)
            st.experimental_rerun()

    with col2:
        if st.button("📥 Download Report", use_container_width=True):
            # In reality, this would generate and download a PDF/JSON report
            st.info("Report download functionality would be implemented here")

    with col3:
        # Show next steps based on validation result
        if validation_result.passed:
            st.success("✅ Ready to proceed to drift detection")
        else:
            st.error("❌ Cannot proceed - validation failed")

    # TODO comments for future integration
    st.markdown("---")
    st.markdown("### 🔧 Future Integration Points")
    st.markdown("""
    - TODO: Connect to actual ValidationService (replace mock)
    - TODO: Integrate with actual Great Expectations validation suite
    - TODO: Show real-time validation progress
    - TODO: Allow users to fix certain validation errors (e.g., add missing metadata)
    - TODO: Store validation results in database for audit trail
    - TODO: Provide option to override certain warnings (with appropriate authorization)
    - TODO: Get request_id from URL parameters or routing system
    """)