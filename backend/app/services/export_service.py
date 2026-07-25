import csv
import io
from typing import List
from app.models.visitor import Visitor

class ExportService:
    """
    Extensible Export Service providing standardized formatted exports for entities (CSV, Excel, PDF).
    Currently supports production-grade CSV generation with future hooks for Excel and PDF renderers.
    """

    @staticmethod
    def generate_csv(headers: List[str], rows: List[dict]) -> str:
        """
        Generate CSV string from header list and dictionary rows.
        """
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(headers)

        for row in rows:
            writer.writerow([row.get(h, "") for h in headers])

        return output.getvalue()

    @staticmethod
    def export_visitors_csv(visitors: List[Visitor]) -> str:

        """
        Generate downloadable CSV data string for a list of Visitor records.
        """
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)

        # CSV Header Row
        writer.writerow([
            "Visitor ID",
            "Tenant ID",
            "Visitor Code",
            "First Name",
            "Last Name",
            "Full Name",
            "Email",
            "Phone",
            "Gender",
            "Date of Birth",
            "Company",
            "Designation",
            "Gov ID Type",
            "Gov ID Number",
            "Emergency Contact Name",
            "Emergency Contact Phone",
            "Verified",
            "Verification Status",
            "Verification Method",
            "Blacklisted",
            "Blacklist Reason",
            "Status",
            "Created At"
        ])

        # Write data rows
        for v in visitors:
            full_name = f"{v.first_name} {v.last_name}"
            writer.writerow([
                v.id,
                v.tenant_id,
                v.visitor_code,
                v.first_name,
                v.last_name,
                full_name,
                v.email or "",
                v.phone,
                v.gender or "",
                str(v.date_of_birth) if v.date_of_birth else "",
                v.company or "",
                v.designation or "",
                v.government_id_type or "",
                v.government_id_number or "",
                v.emergency_contact_name or "",
                v.emergency_contact_phone or "",
                "TRUE" if v.verified else "FALSE",
                v.verification_status.value if v.verification_status else "",
                v.verification_method.value if v.verification_method else "",
                "TRUE" if v.blacklisted else "FALSE",
                v.blacklist_reason or "",
                v.status.value if v.status else "",
                v.created_at.strftime("%Y-%m-%d %H:%M:%S") if v.created_at else ""
            ])

        return output.getvalue()

    @staticmethod
    def export_visitors_excel(visitors: List[Visitor]) -> bytes:
        """
        Hook for future Excel format export (.xlsx).
        """
        raise NotImplementedError("Excel export renderer is scheduled for upcoming release.")

    @staticmethod
    def export_visitors_pdf(visitors: List[Visitor]) -> bytes:
        """
        Hook for future PDF format export (.pdf).
        """
        raise NotImplementedError("PDF export renderer is scheduled for upcoming release.")
