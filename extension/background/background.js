/**
 * Background service worker for Eco-Conscious Shopper extension.
 * Handles background tasks and messaging.
 */

console.log("Eco-Conscious Shopper background service worker loaded");

// Listen for extension installation
chrome.runtime.onInstalled.addListener((details) => {
    console.log("Extension installed:", details.reason);

    if (details.reason === "install") {
        // First time installation
        console.log("First time installation");

        // Set default settings
        chrome.storage.local.set({
            settings: {
                autoAnalyze: false,
                cacheEnabled: true,
            }
        });

        // Open welcome page (optional)
        // chrome.tabs.create({ url: "welcome.html" });
    }
});

// Listen for messages from content scripts or popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log("Background received message:", request);

    if (request.action === "analyzeProduct") {
        handleProductAnalysis(request.productUrl)
            .then(result => sendResponse({ success: true, data: result }))
            .catch(error => sendResponse({ success: false, error: error.message }));

        // Return true to indicate we'll respond asynchronously
        return true;
    }
});

/**
 * Handle product analysis request
 */
async function handleProductAnalysis(productUrl) {
    console.log("Analyzing product:", productUrl);

    // This would call the API endpoint
    // For now, return mock data
    return {
        rating: "B",
        timestamp: new Date().toISOString()
    };
}

// Listen for tab updates (optional: auto-analyze on product pages)
chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
    if (changeInfo.status === "complete" && tab.url) {
        // Check if auto-analyze is enabled
        const settings = await chrome.storage.local.get(["settings"]);

        if (settings.settings?.autoAnalyze) {
            // Check if it's a product page
            // Then trigger analysis
        }
    }
});

// Handle storage changes
chrome.storage.onChanged.addListener((changes, areaName) => {
    console.log("Storage changed:", changes, areaName);
});
