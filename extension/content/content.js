/**
 * Content script for Eco-Conscious Shopper extension.
 * Runs in the context of web pages to detect products and show sustainability badges.
 */

console.log("Eco-Conscious Shopper content script loaded");

// Configuration
const BADGE_CLASS = "eco-badge";
const BADGE_INJECTED_ATTR = "data-eco-badge-injected";

/**
 * Initialize content script
 */
function init() {
    // Detect if we're on a product page
    if (isProductPage()) {
        console.log("Product page detected");
        injectSustainabilityBadge();
    }

    // Listen for messages from background script
    chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
        if (request.action === "getRating") {
            sendResponse({ rating: getCachedRating() });
        }
    });
}

/**
 * Detect if current page is a product page
 */
function isProductPage() {
    // Check for common product page indicators
    const indicators = [
        // Common product page patterns
        /\/product\//i.test(window.location.pathname),
        /\/item\//i.test(window.location.pathname),
        /\/p\//i.test(window.location.pathname),
        /\/dp\//i.test(window.location.pathname),  // Amazon

        // Check for product schema
        document.querySelector('script[type="application/ld+json"]') !== null,

        // Check for "Add to Cart" button
        document.querySelector('[data-test*="add-to-cart"]') !== null ||
        document.querySelector('button[id*="add-to-cart"]') !== null ||
        document.querySelector('.add-to-cart') !== null
    ];

    return indicators.some(indicator => indicator === true);
}

/**
 * Inject sustainability badge on product page
 */
function injectSustainabilityBadge() {
    // Find a suitable place to inject the badge
    const targetElement = findBadgeTarget();

    if (!targetElement || targetElement.getAttribute(BADGE_INJECTED_ATTR)) {
        return;
    }

    // Create badge element
    const badge = createBadge();

    // Inject badge
    targetElement.insertAdjacentElement("afterbegin", badge);
    targetElement.setAttribute(BADGE_INJECTED_ATTR, "true");

    console.log("Sustainability badge injected");
}

/**
 * Find suitable element to inject badge
 */
function findBadgeTarget() {
    // Try various selectors for common product info containers
    const selectors = [
        '[class*="product-info"]',
        '[class*="product-details"]',
        '[id*="product-info"]',
        'h1',  // Product title as fallback
    ];

    for (const selector of selectors) {
        const element = document.querySelector(selector);
        if (element) {
            return element.parentElement;
        }
    }

    return null;
}

/**
 * Create badge element
 */
function createBadge() {
    const badge = document.createElement("div");
    badge.className = BADGE_CLASS;
    badge.innerHTML = `
        <div class="eco-badge-container">
            <div class="eco-badge-icon">🌱</div>
            <div class="eco-badge-text">
                <strong>Sustainability Rating</strong>
                <p>Click extension to view</p>
            </div>
        </div>
    `;

    return badge;
}

/**
 * Get cached rating for this page (if any)
 */
function getCachedRating() {
    // This would retrieve from chrome.storage.local
    // For now, return null
    return null;
}

// Initialize when DOM is ready
if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
} else {
    init();
}
