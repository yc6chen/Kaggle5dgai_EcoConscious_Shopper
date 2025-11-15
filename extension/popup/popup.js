/**
 * Popup script for Eco-Conscious Shopper extension.
 * Handles UI interactions and API communication.
 */

// API configuration
const API_BASE_URL = "http://localhost:8080";  // Update for production deployment

// DOM elements
const loadingSection = document.getElementById("loading");
const errorSection = document.getElementById("error");
const resultsSection = document.getElementById("results");
const initialSection = document.getElementById("initial");

const analyzeBtn = document.getElementById("analyze-btn");
const retryBtn = document.getElementById("retry-btn");

// Initialize
document.addEventListener("DOMContentLoaded", () => {
    console.log("Popup loaded");

    // Set up event listeners
    analyzeBtn.addEventListener("click", analyzeCurrentPage);
    retryBtn.addEventListener("click", analyzeCurrentPage);

    // Check if we have cached results for this tab
    loadCachedResults();
});

/**
 * Analyze the current page/product
 */
async function analyzeCurrentPage() {
    try {
        // Get current tab URL
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

        if (!tab || !tab.url) {
            showError("Unable to get current page URL");
            return;
        }

        const productUrl = tab.url;
        console.log("Analyzing:", productUrl);

        // Show loading state
        showSection("loading");

        // Call API
        const rating = await analyzeProduct(productUrl);

        // Show results
        displayResults(rating, productUrl);

        // Cache results
        await cacheResults(tab.id, rating, productUrl);

    } catch (error) {
        console.error("Analysis error:", error);
        showError(error.message || "Failed to analyze product");
    }
}

/**
 * Call the analysis API
 */
async function analyzeProduct(productUrl) {
    const response = await fetch(`${API_BASE_URL}/api/analyze-product`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            product_url: productUrl
        })
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "API request failed");
    }

    const data = await response.json();
    return data;
}

/**
 * Display analysis results in the popup
 */
function displayResults(analysisResponse, productUrl) {
    const { rating, processing_time_seconds, cached } = analysisResponse;

    // Extract brand from URL
    const brand = extractBrandFromUrl(productUrl);

    // Update brand info
    document.getElementById("brand-name").textContent = brand;
    document.getElementById("product-link").href = productUrl;

    // Update grades
    document.getElementById("overall-grade").textContent = rating.overall_score;
    document.getElementById("overall-grade").className = `grade grade-${rating.overall_score}`;

    document.getElementById("env-grade").textContent = rating.environmental_score;
    document.getElementById("env-grade").className = `grade grade-${rating.environmental_score}`;

    document.getElementById("labor-grade").textContent = rating.labor_score;
    document.getElementById("labor-grade").className = `grade grade-${rating.labor_score}`;

    document.getElementById("trans-grade").textContent = rating.transparency_score;
    document.getElementById("trans-grade").className = `grade grade-${rating.transparency_score}`;

    // Update confidence
    const confidencePercent = Math.round(rating.confidence_score * 100);
    document.getElementById("confidence-score").textContent = `${confidencePercent}%`;

    // Update rationale
    document.getElementById("rationale-overall").textContent = rating.rationale.overall;
    document.getElementById("rationale-env").textContent = rating.rationale.environmental;
    document.getElementById("rationale-labor").textContent = rating.rationale.labor;
    document.getElementById("rationale-trans").textContent = rating.rationale.transparency;

    // Update timestamp
    const timestamp = new Date(rating.research_timestamp);
    document.getElementById("timestamp").textContent =
        `Analyzed: ${timestamp.toLocaleString()}`;

    // Show cached indicator if applicable
    const cachedIndicator = document.getElementById("cached-indicator");
    if (cached) {
        cachedIndicator.classList.remove("hidden");
    } else {
        cachedIndicator.classList.add("hidden");
    }

    // Show results section
    showSection("results");
}

/**
 * Show error message
 */
function showError(message) {
    document.getElementById("error-message").textContent = message;
    showSection("error");
}

/**
 * Show a specific section and hide others
 */
function showSection(sectionName) {
    const sections = [loadingSection, errorSection, resultsSection, initialSection];

    sections.forEach(section => {
        section.classList.add("hidden");
    });

    const sectionMap = {
        "loading": loadingSection,
        "error": errorSection,
        "results": resultsSection,
        "initial": initialSection
    };

    const targetSection = sectionMap[sectionName];
    if (targetSection) {
        targetSection.classList.remove("hidden");
    }
}

/**
 * Extract brand name from URL
 */
function extractBrandFromUrl(url) {
    try {
        const urlObj = new URL(url);
        const domain = urlObj.hostname.replace("www.", "").replace("shop.", "");
        const parts = domain.split(".");
        return parts[0].charAt(0).toUpperCase() + parts[0].slice(1);
    } catch {
        return "Unknown Brand";
    }
}

/**
 * Cache results for this tab
 */
async function cacheResults(tabId, rating, productUrl) {
    try {
        await chrome.storage.local.set({
            [`tab_${tabId}`]: {
                rating,
                productUrl,
                timestamp: Date.now()
            }
        });
    } catch (error) {
        console.error("Failed to cache results:", error);
    }
}

/**
 * Load cached results for current tab
 */
async function loadCachedResults() {
    try {
        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

        if (!tab) return;

        const result = await chrome.storage.local.get([`tab_${tab.id}`]);
        const cached = result[`tab_${tab.id}`];

        if (cached && cached.rating) {
            // Check if cache is still fresh (< 1 hour)
            const age = Date.now() - cached.timestamp;
            if (age < 3600000) {
                displayResults(
                    { rating: cached.rating, cached: true },
                    cached.productUrl
                );
            }
        }
    } catch (error) {
        console.error("Failed to load cached results:", error);
    }
}
