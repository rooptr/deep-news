rule suspicious_pdf_active_content {
    meta:
        description = "PDF contains active or embedded content requiring review"
        severity = "medium"
    strings:
        $pdf = "%PDF-" ascii
        $javascript = "/JavaScript" ascii nocase
        $js = "/JS" ascii
        $launch = "/Launch" ascii nocase
        $open_action = "/OpenAction" ascii nocase
        $embedded = "/EmbeddedFile" ascii nocase
        $rich_media = "/RichMedia" ascii nocase
    condition:
        $pdf at 0 and 1 of ($javascript, $js, $launch, $open_action, $embedded, $rich_media)
}
