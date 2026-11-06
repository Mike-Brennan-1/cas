import base64
from io import BytesIO

import streamlit as st
from PIL import Image

IMAGE_KEY = "sim_image"

PASTE_HTML = """
<button type="button">Paste from clipboard</button>
<p>or press Ctrl+V / ⌘V anywhere on this page</p>
"""

PASTE_CSS = """
button {
    width: 100%;
    padding: 0.4rem 0.75rem;
    font: inherit;
    font-size: 0.875rem;
    color: var(--st-text-color);
    background: var(--st-background-color);
    border: 1px solid var(--st-border-color);
    border-radius: var(--st-base-radius);
    cursor: pointer;
}
button:hover {
    color: var(--st-primary-color);
    border-color: var(--st-primary-color);
}
p {
    margin: 0.25rem 0 0;
    font-size: 0.8rem;
    color: var(--st-text-color);
    opacity: 0.7;
}
"""

PASTE_JS = """
export default function ({ parentElement, setTriggerValue }) {
    const button = parentElement.querySelector("button");
    const status = parentElement.querySelector("p");

    const send = (blob) => {
        const reader = new FileReader();
        reader.onload = () => setTriggerValue("pasted", reader.result);
        reader.readAsDataURL(blob);
    };

    // navigator.clipboard only exists on https or localhost. Ctrl+V works anywhere.
    button.hidden = !navigator.clipboard?.read;
    button.onclick = async () => {
        try {
            for (const item of await navigator.clipboard.read()) {
                const type = item.types.find((t) => t.startsWith("image/"));
                if (type) return send(await item.getType(type));
            }
            status.textContent = "No image on the clipboard. Copy one and try again.";
        } catch {
            status.textContent = "Clipboard access was blocked. Try Ctrl+V / ⌘V instead.";
        }
    };

    const onPaste = (event) => {
        const { files, types } = event.clipboardData;
        const image = [...files].find((file) => file.type.startsWith("image/"));
        // Copying from Excel or Word puts text and an image on the clipboard, so
        // leave that alone when the user is pasting into a text field.
        const inTextField = event.target.closest?.("input, textarea, [contenteditable]");
        if (image && !(inTextField && types.includes("text/plain"))) send(image);
    };
    document.addEventListener("paste", onPaste);
    return () => document.removeEventListener("paste", onPaste);
}
"""

paste_image = st.components.v2.component(
    "sim_image_paste", html=PASTE_HTML, css=PASTE_CSS, js=PASTE_JS
)


def _is_image(data: bytes) -> bool:
    try:
        Image.open(BytesIO(data)).verify()
    except Exception:  # Pillow raises many types on bad data, including SyntaxError.
        return False
    return True


def _clear_image() -> None:
    del st.session_state[IMAGE_KEY]


def sim_image_input() -> bytes | None:
    """Show the sim's image, or the upload and paste controls if there isn't one."""
    if image := st.session_state.get(IMAGE_KEY):
        st.image(image, width="stretch", alt="Sim image")
        st.button("Remove image", on_click=_clear_image, width="stretch")
        return image

    uploaded = st.file_uploader("Sim image", type=["png", "jpg", "jpeg", "webp"])
    pasted = paste_image(key="sim_image_paste", on_pasted_change=lambda: None).pasted

    if uploaded:
        data = uploaded.getvalue()
    elif pasted:
        data = base64.b64decode(pasted.partition(",")[2])
    else:
        return None

    if not _is_image(data):
        st.error("That file couldn't be read as an image.")
        return None

    st.session_state[IMAGE_KEY] = data
    st.rerun()
