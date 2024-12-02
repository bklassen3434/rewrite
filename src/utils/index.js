/**
 * TODO
 * @param {*} element 
 */
export function wrapTextNodesInBlockElements(element) {
  Array.from(element.childNodes).forEach((node) => {
    if (node.nodeType === Node.TEXT_NODE && node.textContent.trim() !== "") {
      const p = document.createElement("p");
      p.textContent = node.textContent.trim();
      element.replaceChild(p, node);
    }
  });
}

/**
 * TODO
 * @param {*} ms 
 * @returns 
 */
export function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * TODO
 * @param {*} text 
 * @returns 
 */
export function normalizeText(text) {
  return text
    .toLowerCase()
    .replace(/[^\w\s]/g, "")
    .trim(); // Remove special characters and convert to lowercase
}
