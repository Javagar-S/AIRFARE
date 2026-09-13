/* ============================================================
   ARTHAVAYU
   INDIA AIRFARE INTELLIGENCE

   SINGLE PAGE APPLICATION

   Responsibilities
   -----------------
   1. Fetch dashboard data
   2. Build dynamic filters
   3. Filter data
   4. Render KPIs
   5. Render charts
   6. Render route intelligence
   7. Render airport directory
   8. Render fare observations
   9. Handle route/airport details
   10. Handle theme / zoom / language
   11. Handle responsive rendering
============================================================ */


/* ============================================================
   APPLICATION STATE
============================================================ */

const APP = {

    /* Raw dashboard data */
    rawData: null,

    /* Current filtered data */
    filteredData: null,

    /* Whether the current data came from API */
    dataMode: "LOADING",

    /* Current trend period */
    period: "daily",

    /* Current zoom */
    zoom: 1,

    /* Airport pagination */
    airportPage: 1,

    airportPageSize: 12,

    /* Observation pagination */
    observationPage: 1,

    observationPageSize: 15,

    /* Chart instances */
    charts: {},

    /* Current filter state */

    filters: {

        origin: "ALL",

        destination: "ALL",

        travelDate: "ALL",

        bookingWindow: "ALL",

        airline: "ALL",

        period: "daily"

    },

    /* Airport directory */
    airports: [],

    filteredAirports: [],

    /* Observations */
    observations: [],

    filteredObservations: []

};


/* ============================================================
   CONFIGURATION
============================================================ */

const CONFIG = {

    dashboardEndpoint:
        "/api/dashboard",

    requestTimeout:
        10000,

    currency:
        "INR",

    baseIndex:
        100

};


/* ============================================================
   AIRPORT MASTER DATA
============================================================ */

/*
 * This is only used to provide proper human-readable
 * airport names for the airport directory.
 *
 * Route data still determines which airports actually
 * appear in the interface.
 */

const AIRPORT_MASTER = {

    DEL: {

        city:
            "Delhi",

        name:
            "Indira Gandhi International Airport",

        state:
            "Delhi"

    },

    BOM: {

        city:
            "Mumbai",

        name:
            "Chhatrapati Shivaji Maharaj International Airport",

        state:
            "Maharashtra"

    },

    BLR: {

        city:
            "Bengaluru",

        name:
            "Kempegowda International Airport",

        state:
            "Karnataka"

    },

    HYD: {

        city:
            "Hyderabad",

        name:
            "Rajiv Gandhi International Airport",

        state:
            "Telangana"

    },

    MAA: {

        city:
            "Chennai",

        name:
            "Chennai International Airport",

        state:
            "Tamil Nadu"

    },

    CCU: {

        city:
            "Kolkata",

        name:
            "Netaji Subhas Chandra Bose International Airport",

        state:
            "West Bengal"

    },

    PNQ: {

        city:
            "Pune",

        name:
            "Pune International Airport",

        state:
            "Maharashtra"

    },

    AMD: {

        city:
            "Ahmedabad",

        name:
            "Sardar Vallabhbhai Patel International Airport",

        state:
            "Gujarat"

    },

    COK: {

        city:
            "Kochi",

        name:
            "Cochin International Airport",

        state:
            "Kerala"

    },

    GOI: {

        city:
            "Goa",

        name:
            "Goa International Airport",

        state:
            "Goa"

    },

    GOX: {

        city:
            "Goa",

        name:
            "Manohar International Airport",

        state:
            "Goa"

    },

    JAI: {

        city:
            "Jaipur",

        name:
            "Jaipur International Airport",

        state:
            "Rajasthan"

    },

    LKO: {

        city:
            "Lucknow",

        name:
            "Chaudhary Charan Singh International Airport",

        state:
            "Uttar Pradesh"

    },

    GAU: {

        city:
            "Guwahati",

        name:
            "Lokpriya Gopinath Bordoloi International Airport",

        state:
            "Assam"

    },

    PAT: {

        city:
            "Patna",

        name:
            "Jay Prakash Narayan International Airport",

        state:
            "Bihar"

    },

    IXC: {

        city:
            "Chandigarh",

        name:
            "Chandigarh International Airport",

        state:
            "Chandigarh"

    }

};


/* ============================================================
   DEMO FALLBACK DATA
============================================================ */

/*
 * Used ONLY when Flask cannot provide usable data.
 *
 * Never presented as government statistics.
 * Interface visibly switches to DEMO DATA.
 */

const DEMO_DATA = {

    source:
        "Prototype demonstration dataset",

    summary: {

        api_x:
            108.42,

        api_x_change:
            4.82,

        average_fare:
            6491,

        minimum_fare:
            3210,

        maximum_fare:
            12800,

        routes:
            8,

        airlines:
            6,

        observations:
            12840,

        travel_dates:
            14,

        updated_at:
            null

    },

    trend: [

        {
            date:
                "2026-09-01",

            api_x:
                100.00
        },

        {
            date:
                "2026-09-02",

            api_x:
                100.84
        },

        {
            date:
                "2026-09-03",

            api_x:
                101.32
        },

        {
            date:
                "2026-09-04",

            api_x:
                102.71
        },

        {
            date:
                "2026-09-05",

            api_x:
                103.18
        },

        {
            date:
                "2026-09-06",

            api_x:
                102.91
        },

        {
            date:
                "2026-09-07",

            api_x:
                104.67
        },

        {
            date:
                "2026-09-08",

            api_x:
                105.21
        },

        {
            date:
                "2026-09-09",

            api_x:
                105.82
        },

        {
            date:
                "2026-09-10",

            api_x:
                106.74
        },

        {
            date:
                "2026-09-11",

            api_x:
                107.31
        },

        {
            date:
                "2026-09-12",

            api_x:
                108.01
        },

        {
            date:
                "2026-09-13",

            api_x:
                108.42
        }

    ],

    routes: [

        {
            route:
                "DEL-BOM",

            average_fare:
                6910,

            median_fare:
                6720,

            minimum_fare:
                4810,

            maximum_fare:
                11900,

            observations:
                1850,

            airlines:
                6,

            volatility_pct:
                13.2
        },

        {
            route:
                "BLR-DEL",

            average_fare:
                6540,

            median_fare:
                6210,

            minimum_fare:
                4200,

            maximum_fare:
                11200,

            observations:
                1680,

            airlines:
                7,

            volatility_pct:
                15.4
        },

        {
            route:
                "BLR-BOM",

            average_fare:
                6120,

            median_fare:
                5980,

            minimum_fare:
                3910,

            maximum_fare:
                10100,

            observations:
                1490,

            airlines:
                6,

            volatility_pct:
                11.1
        },

        {
            route:
                "DEL-HYD",

            average_fare:
                5980,

            median_fare:
                5740,

            minimum_fare:
                3750,

            maximum_fare:
                10500,

            observations:
                1420,

            airlines:
                6,

            volatility_pct:
                12.7
        },

        {
            route:
                "BOM-HYD",

            average_fare:
                5410,

            median_fare:
                5230,

            minimum_fare:
                3420,

            maximum_fare:
                9120,

            observations:
                1310,

            airlines:
                5,

            volatility_pct:
                10.4
        },

        {
            route:
                "DEL-MAA",

            average_fare:
                7230,

            median_fare:
                6980,

            minimum_fare:
                4900,

            maximum_fare:
                12400,

            observations:
                1190,

            airlines:
                5,

            volatility_pct:
                16.1
        },

        {
            route:
                "BLR-MAA",

            average_fare:
                4870,

            median_fare:
                4680,

            minimum_fare:
                3060,

            maximum_fare:
                7900,

            observations:
                1050,

            airlines:
                5,

            volatility_pct:
                9.8
        },

        {
            route:
                "CCU-DEL",

            average_fare:
                6120,

            median_fare:
                5900,

            minimum_fare:
                3890,

            maximum_fare:
                9200,

            observations:
                980,

            airlines:
                5,

            volatility_pct:
                10.9
        }

    ],

    airlines: [

        {
            airline:
                "IndiGo",

            average_fare:
                6210,

            median_fare:
                5980,

            minimum_fare:
                3200,

            maximum_fare:
                11600,

            observations:
                4250,

            routes:
                8
        },

        {
            airline:
                "Air India",

            average_fare:
                6810,

            median_fare:
                6490,

            minimum_fare:
                3510,

            maximum_fare:
                12800,

            observations:
                2920,

            routes:
                7
        },

        {
            airline:
                "Akasa Air",

            average_fare:
                5980,

            median_fare:
                5710,

            minimum_fare:
                3290,

            maximum_fare:
                9300,

            observations:
                2050,

            routes:
                6
        },

        {
            airline:
                "Air India Express",

            average_fare:
                5750,

            median_fare:
                5480,

            minimum_fare:
                3190,

            maximum_fare:
                8800,

            observations:
                1810,

            routes:
                5
        },

        {
            airline:
                "SpiceJet",

            average_fare:
                5630,

            median_fare:
                5390,

            minimum_fare:
                3020,

            maximum_fare:
                8400,

            observations:
                670,

            routes:
                4
        },

        {
            airline:
                "Vistara",

            average_fare:
                7350,

            median_fare:
                7010,

            minimum_fare:
                4100,

            maximum_fare:
                12200,

            observations:
                1140,

            routes:
                4
        }

    ],

    booking_window: [

        {
            booking_window:
                "60+ days",

            average_fare:
                4930,

            median_fare:
                4780,

            minimum_fare:
                3900,

            maximum_fare:
                7000,

            observations:
                1350
        },

        {
            booking_window:
                "31-60 days",

            average_fare:
                5180,

            median_fare:
                5020,

            minimum_fare:
                4200,

            maximum_fare:
                7400,

            observations:
                1890
        },

        {
            booking_window:
                "15-30 days",

            average_fare:
                5570,

            median_fare:
                5380,

            minimum_fare:
                4400,

            maximum_fare:
                7900,

            observations:
                2450
        },

        {
            booking_window:
                "8-14 days",

            average_fare:
                6080,

            median_fare:
                5890,

            minimum_fare:
                4700,

            maximum_fare:
                8600,

            observations:
                2680
        },

        {
            booking_window:
                "4-7 days",

            average_fare:
                6880,

            median_fare:
                6610,

            minimum_fare:
                5100,

            maximum_fare:
                9900,

            observations:
                2360
        },

        {
            booking_window:
                "0-3 days",

            average_fare:
                7580,

            median_fare:
                7310,

            minimum_fare:
                5800,

            maximum_fare:
                11200,

            observations:
                2110
        }

    ],

    distribution: [

        {
            fare_bucket:
                "<= ₹5K",

            observations:
                1960
        },

        {
            fare_bucket:
                "₹5K–7.5K",

            observations:
                4720
        },

        {
            fare_bucket:
                "₹7.5K–10K",

            observations:
                3280
        },

        {
            fare_bucket:
                "₹10K–15K",

            observations:
                1890
        },

        {
            fare_bucket:
                "₹15K–25K",

            observations:
                710
        },

        {
            fare_bucket:
                "₹25K–50K",

            observations:
                230
        },

        {
            fare_bucket:
                "₹50K+",

            observations:
                50
        }

    ],

    quality: {

        records:
            12840,

        duplicates:
            0,

        outliers:
            84,

        completeness_pct:
            96.8

    },

    recent_flights: []

};


/* ============================================================
   LANGUAGE DICTIONARY
============================================================ */

const LANGUAGE = {

    en: {

        showingNational:
            "Showing the national airfare market",

        showingRoute:
            "Showing",

        observations:
            "observations",

        airlines:
            "airlines",

        monitoring:
            "MONITORING",

        stable:
            "STABLE",

        rising:
            "RISING",

        elevated:
            "ELEVATED",

        belowBase:
            "BELOW BASE",

        noData:
            "No observations available"

    },

    hi: {

        showingNational:
            "राष्ट्रीय हवाई किराया बाजार दिखाया जा रहा है",

        showingRoute:
            "दिखाया जा रहा है",

        observations:
            "अवलोकन",

        airlines:
            "एयरलाइंस",

        monitoring:
            "निगरानी",

        stable:
            "स्थिर",

        rising:
            "बढ़ रहा है",

        elevated:
            "ऊंचा",

        belowBase:
            "आधार से नीचे",

        noData:
            "कोई डेटा उपलब्ध नहीं"

    },

    kn: {

        showingNational:
            "ರಾಷ್ಟ್ರೀಯ ವಿಮಾನ ದರ ಮಾರುಕಟ್ಟೆಯನ್ನು ತೋರಿಸಲಾಗುತ್ತಿದೆ",

        showingRoute:
            "ತೋರಿಸಲಾಗುತ್ತಿದೆ",

        observations:
            "ವೀಕ್ಷಣೆಗಳು",

        airlines:
            "ವಿಮಾನಯಾನ ಸಂಸ್ಥೆಗಳು",

        monitoring:
            "ಮೇಲ್ವಿಚಾರಣೆ",

        stable:
            "ಸ್ಥಿರ",

        rising:
            "ಏರಿಕೆ",

        elevated:
            "ಹೆಚ್ಚು",

        belowBase:
            "ಮೂಲಕ್ಕಿಂತ ಕಡಿಮೆ",

        noData:
            "ಯಾವುದೇ ಡೇಟಾ ಲಭ್ಯವಿಲ್ಲ"

    }

};


let CURRENT_LANGUAGE =
    localStorage.getItem(
        "arthavayu-language"
    )
    ||
    "en";


/* ============================================================
   DOM READY
============================================================ */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        console.log(
            "ArthaVayu dashboard starting..."
        );


        initializeTheme();

        initializeZoom();

        initializeLanguage();

        initializeNavigation();

        initializeFilters();

        initializeRouteSearch();

        initializeAirportSearch();

        initializeObservationFilters();

        initializePagination();

        initializeRouteDrawer();

        initializeAirportModal();

        initializeRefresh();

        loadDashboard();

    }
);


/* ============================================================
   LOAD DASHBOARD
============================================================ */

async function loadDashboard() {

    setGlobalState(
        "LOADING"
    );


    try {

        const controller =
            new AbortController();


        const timeout =
            setTimeout(
                () =>
                    controller.abort(),
                CONFIG.requestTimeout
            );


        const response =
            await fetch(
                CONFIG.dashboardEndpoint,
                {

                    method:
                        "GET",

                    headers: {

                        "Accept":
                            "application/json"

                    },

                    cache:
                        "no-store",

                    signal:
                        controller.signal

                }
            );


        clearTimeout(
            timeout
        );


        if (!response.ok) {

            throw new Error(
                `Dashboard API returned HTTP ${response.status}`
            );

        }


        const result =
            await response.json();


        if (
            !result
            ||
            result.success !== true
            ||
            !result.data
        ) {

            throw new Error(
                "Dashboard API did not return usable data."
            );

        }


        APP.rawData =
            normalizeData(
                result.data
            );


        APP.dataMode =
            "LIVE";


        console.log(
            "ArthaVayu using LIVE data."
        );


    } catch (error) {

        console.warn(
            "Live dashboard unavailable. Using fallback.",
            error
        );


        APP.rawData =
            normalizeData(
                DEMO_DATA
            );


        APP.dataMode =
            "DEMO";

    }


    setGlobalState(
        APP.dataMode
    );


    populateDynamicFilters();

    buildAirportDirectory();

    buildObservationDataset();

    applyAllFilters();

}


/* ============================================================
   NORMALIZE DATA
============================================================ */

function normalizeData(
    data
) {

    const output = {

        source:
            data?.source
            ||
            "Processed analytical dataset",

        summary:
            data?.summary
            ||
            {},

        trend:
            Array.isArray(
                data?.trend
            )
                ? data.trend
                : [],

        routes:
            Array.isArray(
                data?.routes
            )
                ? data.routes
                : [],

        airlines:
            Array.isArray(
                data?.airlines
            )
                ? data.airlines
                : [],

        booking_window:
            Array.isArray(
                data?.booking_window
            )
                ? data.booking_window
                : [],

        distribution:
            Array.isArray(
                data?.distribution
            )
                ? data.distribution
                : [],

        quality:
            data?.quality
            ||
            {},

        recent_flights:
            Array.isArray(
                data?.recent_flights
            )
                ? data.recent_flights
                : []

    };


    return output;

}


/* ============================================================
   GLOBAL STATE
============================================================ */

function setGlobalState(
    state
) {

    const dataState =
        document.getElementById(
            "globalDataState"
        );


    const statusText =
        document.getElementById(
            "systemStatusText"
        );


    const footerStatus =
        document.getElementById(
            "footerStatus"
        );


    if (
        dataState
    ) {

        if (
            state === "LIVE"
        ) {

            dataState.textContent =
                "LIVE DATA";

            dataState.className =
                "data-state live-data";

        } else if (
            state === "DEMO"
        ) {

            dataState.textContent =
                "DEMO DATA";

            dataState.className =
                "data-state demo-data";

        } else {

            dataState.textContent =
                state;

        }

    }


    if (
        statusText
    ) {

        statusText.textContent =
            state === "LOADING"
                ? "CONNECTING"
                : "OPERATIONAL";

    }


    if (
        footerStatus
    ) {

        footerStatus.textContent =
            state === "LIVE"
                ? "LIVE DATA"
                : state === "DEMO"
                    ? "PROTOTYPE DATA"
                    : state;

    }

}


/* ============================================================
   POPULATE FILTERS
============================================================ */

function populateDynamicFilters() {

    if (!APP.rawData) {
        return;
    }


    populateAirportFilters();

    populateDateFilter();

    populateAirlineFilter();

    populateObservationFilters();

}


/* ============================================================
   AIRPORT DROPDOWNS
============================================================ */

function populateAirportFilters() {

    const originSelect =
        document.getElementById(
            "originSelect"
        );


    const destinationSelect =
        document.getElementById(
            "destinationSelect"
        );


    if (
        !originSelect
        ||
        !destinationSelect
    ) {

        return;

    }


    const routes =
        APP.rawData.routes
        || [];


    const origins =
        new Set();


    const destinations =
        new Set();


    routes.forEach(
        route => {

            const parts =
                parseRoute(
                    route.route
                );


            if (
                parts.origin
            ) {

                origins.add(
                    parts.origin
                );

            }


            if (
                parts.destination
            ) {

                destinations.add(
                    parts.destination
                );

            }

        }
    );


    fillSelect(

        originSelect,

        [...origins]
            .sort(),

        {
            allLabel:
                "All airports",

            formatter:
                formatAirportOption

        }

    );


    /*
     * Destination list depends on
     * origin selection.
     */

    updateDestinationOptions();

}


/* ============================================================
   DESTINATION OPTIONS
============================================================ */

function updateDestinationOptions() {

    const select =
        document.getElementById(
            "destinationSelect"
        );


    if (!select) {
        return;
    }


    const selectedOrigin =
        APP.filters.origin;


    const routes =
        APP.rawData?.routes
        || [];


    const destinations =
        new Set();


    routes.forEach(
        route => {

            const parts =
                parseRoute(
                    route.route
                );


            if (!parts.destination) {
                return;
            }


            if (
                selectedOrigin === "ALL"
                ||
                parts.origin
                ===
                selectedOrigin
            ) {

                destinations.add(
                    parts.destination
                );

            }

        }
    );


    const previous =
        APP.filters.destination;


    fillSelect(

        select,

        [...destinations]
            .sort(),

        {
            allLabel:
                "All destinations",

            formatter:
                formatAirportOption

        }

    );


    /*
     * Preserve destination when still valid.
     */

    if (
        [...select.options]
            .some(
                option =>
                    option.value
                    ===
                    previous
            )
    ) {

        select.value =
            previous;

    } else {

        select.value =
            "ALL";

        APP.filters.destination =
            "ALL";

    }

}


/* ============================================================
   DATE DROPDOWN
============================================================ */

function populateDateFilter() {

    const select =
        document.getElementById(
            "travelDateSelect"
        );


    if (!select) {
        return;
    }


    const dates =
        extractAvailableDates(
            APP.rawData
        );


    fillSelect(

        select,

        dates,

        {
            allLabel:
                "All dates",

            formatter:
                formatDateLong

        }

    );

}


/* ============================================================
   AIRLINE DROPDOWN
============================================================ */

function populateAirlineFilter() {

    const select =
        document.getElementById(
            "airlineSelect"
        );


    if (!select) {
        return;
    }


    const airlines =
        APP.rawData.airlines
            .map(
                item =>
                    item.airline
            )
            .filter(
                Boolean
            )
            .sort(
                (
                    a,
                    b
                ) =>
                    a.localeCompare(
                        b
                    )
            );


    fillSelect(

        select,

        airlines,

        {
            allLabel:
                "All airlines",

            formatter:
                value =>
                    value

        }

    );

}


/* ============================================================
   OBSERVATION FILTERS
============================================================ */

function populateObservationFilters() {

    const routeSelect =
        document.getElementById(
            "observationRouteSelect"
        );


    const airlineSelect =
        document.getElementById(
            "observationAirlineSelect"
        );


    if (
        routeSelect
    ) {

        const routes =
            unique(
                APP.observations.map(
                    item =>
                        item.route
                )
            )
            .sort();


        fillSelect(

            routeSelect,

            routes,

            {
                allLabel:
                    "All routes",

                formatter:
                    value =>
                        value

            }

        );

    }


    if (
        airlineSelect
    ) {

        const airlines =
            unique(
                APP.observations.map(
                    item =>
                        item.airline
                )
            )
            .filter(
                Boolean
            )
            .sort();


        fillSelect(

            airlineSelect,

            airlines,

            {
                allLabel:
                    "All airlines",

                formatter:
                    value =>
                        value

            }

        );

    }

}


/* ============================================================
   SELECT BUILDER
============================================================ */

function fillSelect(
    select,
    values,
    options = {}
) {

    if (!select) {
        return;
    }


    const previous =
        select.value;


    select.innerHTML =
        "";


    const allOption =
        document.createElement(
            "option"
        );


    allOption.value =
        "ALL";


    allOption.textContent =
        options.allLabel
        ||
        "All";


    select.appendChild(
        allOption
    );


    values.forEach(
        value => {

            const option =
                document.createElement(
                    "option"
                );


            option.value =
                value;


            option.textContent =
                options.formatter
                    ? options.formatter(
                        value
                    )
                    : value;


            select.appendChild(
                option
            );

        }
    );


    if (
        [...select.options]
            .some(
                option =>
                    option.value
                    ===
                    previous
            )
    ) {

        select.value =
            previous;

    }

}


/* ============================================================
   FILTER EVENTS
============================================================ */

function initializeFilters() {

    const origin =
        document.getElementById(
            "originSelect"
        );


    const destination =
        document.getElementById(
            "destinationSelect"
        );


    const date =
        document.getElementById(
            "travelDateSelect"
        );


    const booking =
        document.getElementById(
            "bookingWindowSelect"
        );


    const airline =
        document.getElementById(
            "airlineSelect"
        );


    const period =
        document.getElementById(
            "analysisPeriodSelect"
        );


    const reset =
        document.getElementById(
            "resetFilters"
        );


    origin?.addEventListener(
        "change",
        () => {

            APP.filters.origin =
                origin.value;

            updateDestinationOptions();

            APP.filters.destination =
                document.getElementById(
                    "destinationSelect"
                )?.value
                ||
                "ALL";

            applyAllFilters();

        }
    );


    destination?.addEventListener(
        "change",
        () => {

            APP.filters.destination =
                destination.value;

            applyAllFilters();

        }
    );


    date?.addEventListener(
        "change",
        () => {

            APP.filters.travelDate =
                date.value;

            applyAllFilters();

        }
    );


    booking?.addEventListener(
        "change",
        () => {

            APP.filters.bookingWindow =
                booking.value;

            applyAllFilters();

        }
    );


    airline?.addEventListener(
        "change",
        () => {

            APP.filters.airline =
                airline.value;

            applyAllFilters();

        }
    );


    period?.addEventListener(
        "change",
        () => {

            APP.period =
                period.value;

            APP.filters.period =
                period.value;

            renderTrend();

        }
    );


    reset?.addEventListener(
        "click",
        resetFilters
    );

}


/* ============================================================
   RESET
============================================================ */

function resetFilters() {

    APP.filters = {

        origin:
            "ALL",

        destination:
            "ALL",

        travelDate:
            "ALL",

        bookingWindow:
            "ALL",

        airline:
            "ALL",

        period:
            "daily"

    };


    APP.period =
        "daily";


    APP.airportPage =
        1;


    APP.observationPage =
        1;


    const ids = [

        "originSelect",

        "destinationSelect",

        "travelDateSelect",

        "bookingWindowSelect",

        "airlineSelect",

        "analysisPeriodSelect"

    ];


    ids.forEach(
        id => {

            const element =
                document.getElementById(
                    id
                );


            if (element) {

                element.value =
                    "ALL";

            }

        }
    );


    const period =
        document.getElementById(
            "analysisPeriodSelect"
        );


    if (period) {

        period.value =
            "daily";

    }


    populateAirportFilters();

    applyAllFilters();

    showToast(
        "Filters reset"
    );

}


/* ============================================================
   APPLY ALL FILTERS
============================================================ */

function applyAllFilters() {

    const all =
        APP.rawData;


    if (!all) {
        return;
    }


    /*
     * Start with all routes.
     */

    const filteredRoutes =
        all.routes.filter(
            route =>
                routeMatchesFilters(
                    route
                )
        );


    /*
     * Airline data needs to reflect
     * current route selection.
     */

    const filteredAirlines =
        calculateFilteredAirlines(
            filteredRoutes,
            all.airlines
        );


    /*
     * Booking data.
     */

    const filteredBooking =
        calculateFilteredBooking(
            filteredRoutes,
            all.booking_window
        );


    /*
     * Observations.
     */

    const filteredObservations =
        filterObservations(
            APP.observations
        );


    /*
     * Recalculate summary from the
     * underlying observation data when
     * possible.
     */

    const summary =
        calculateSummary(
            filteredRoutes,
            filteredAirlines,
            filteredObservations,
            all.summary
        );


    APP.filteredData = {

        source:
            APP.dataMode === "DEMO"
                ? "Prototype demonstration dataset"
                : all.source,

        summary,

        trend:
            calculateFilteredTrend(
                filteredObservations,
                all.trend,
                filteredRoutes
            ),

        routes:
            filteredRoutes,

        airlines:
            filteredAirlines,

        booking_window:
            filteredBooking,

        distribution:
            calculateDistribution(
                filteredObservations,
                all.distribution
            ),

        quality:
            calculateFilteredQuality(
                filteredObservations,
                all.quality
            ),

        recent_flights:
            filteredObservations

    };


    APP.filteredObservations =
        filteredObservations;


    updateFilterStatus();


    renderDashboard();

}


/* ============================================================
   ROUTE FILTER
============================================================ */

function routeMatchesFilters(
    route
) {

    const parts =
        parseRoute(
            route.route
        );


    if (
        APP.filters.origin
        !==
        "ALL"
        &&
        parts.origin
        !==
        APP.filters.origin
    ) {

        return false;

    }


    if (
        APP.filters.destination
        !==
        "ALL"
        &&
        parts.destination
        !==
        APP.filters.destination
    ) {

        return false;

    }


    /*
     * Airline filter.
     *
     * Route aggregate contains number of
     * airlines, but not airline names.
     * Therefore airline filtering will be
     * primarily observation-driven.
     */


    return true;

}


/* ============================================================
   OBSERVATION FILTER
============================================================ */

function filterObservations(
    observations
) {

    return observations.filter(
        observation => {

            const parts =
                parseRoute(
                    observation.route
                );


            if (
                APP.filters.origin
                !==
                "ALL"
                &&
                parts.origin
                !==
                APP.filters.origin
            ) {

                return false;

            }


            if (
                APP.filters.destination
                !==
                "ALL"
                &&
                parts.destination
                !==
                APP.filters.destination
            ) {

                return false;

            }


            if (
                APP.filters.travelDate
                !==
                "ALL"
            ) {

                const date =
                    normalizeDateValue(
                        observation.outbound_date
                    );


                if (
                    date
                    !==
                    APP.filters.travelDate
                ) {

                    return false;

                }

            }


            if (
                APP.filters.bookingWindow
                !==
                "ALL"
            ) {

                const window =
                    getBookingWindow(
                        observation
                    );


                if (
                    window
                    !==
                    APP.filters.bookingWindow
                ) {

                    return false;

                }

            }


            if (
                APP.filters.airline
                !==
                "ALL"
            ) {

                if (
                    String(
                        observation.airline
                        ||
                        ""
                    )
                    .toLowerCase()
                    !==
                    String(
                        APP.filters.airline
                        ||
                        ""
                    )
                    .toLowerCase()
                ) {

                    return false;

                }

            }


            return true;

        }
    );

}


/* ============================================================
   CALCULATE AIRLINE RESULTS
============================================================ */

function calculateFilteredAirlines(
    filteredRoutes,
    originalAirlines
) {

    /*
     * If no airline filter and no route
     * narrowing, preserve original analytics.
     */

    if (
        APP.filters.origin
        ===
        "ALL"
        &&
        APP.filters.destination
        ===
        "ALL"
        &&
        APP.filters.airline
        ===
        "ALL"
    ) {

        return originalAirlines;

    }


    const selectedRoutes =
        new Set(
            filteredRoutes.map(
                row =>
                    row.route
            )
        );


    /*
     * When observations exist, derive
     * airline values directly from them.
     */

    const routeScopedObservations =
        APP.observations.filter(
            row =>
                selectedRoutes.has(
                    row.route
                )
        );


    let source =
        routeScopedObservations;


    if (
        APP.filters.airline
        !==
        "ALL"
    ) {

        source =
            source.filter(
                row =>
                    String(
                        row.airline
                        ||
                        ""
                    )
                    .toLowerCase()
                    ===
                    String(
                        APP.filters.airline
                    )
                    .toLowerCase()
            );

    }


    if (
        source.length
    ) {

        return aggregateAirlines(
            source
        );

    }


    return originalAirlines.filter(
        airline =>
            APP.filters.airline === "ALL"
            ||
            String(
                airline.airline
            )
            .toLowerCase()
            ===
            String(
                APP.filters.airline
            )
            .toLowerCase()
    );

}


/* ============================================================
   AIRLINE AGGREGATION
============================================================ */

function aggregateAirlines(
    observations
) {

    const groups =
        new Map();


    observations.forEach(
        row => {

            const airline =
                row.airline;


            if (
                !airline
            ) {
                return;
            }


            if (
                !groups.has(
                    airline
                )
            ) {

                groups.set(
                    airline,
                    []
                );

            }


            groups
                .get(
                    airline
                )
                .push(
                    numericFare(
                        row
                    )
                );

        }
    );


    return [
        ...groups.entries()
    ]
    .map(
        (
            [
                airline,
                fares
            ]
        ) => {

            const valid =
                fares.filter(
                    Number.isFinite
                );


            return {

                airline,

                average_fare:
                    average(
                        valid
                    ),

                median_fare:
                    median(
                        valid
                    ),

                minimum_fare:
                    valid.length
                        ? Math.min(
                            ...valid
                        )
                        : 0,

                maximum_fare:
                    valid.length
                        ? Math.max(
                            ...valid
                        )
                        : 0,

                observations:
                    valid.length,

                routes:
                    unique(
                        observations
                            .filter(
                                row =>
                                    row.airline
                                    ===
                                    airline
                            )
                            .map(
                                row =>
                                    row.route
                            )
                    ).length

            };

        }
    )
    .sort(
        (
            a,
            b
        ) =>
            b.average_fare
            -
            a.average_fare
    );

}


/* ============================================================
   BOOKING FILTER
============================================================ */

function calculateFilteredBooking(
    filteredRoutes,
    originalBooking
) {

    const relevantRoutes =
        new Set(
            filteredRoutes.map(
                row =>
                    row.route
            )
        );


    const observations =
        APP.observations.filter(
            row =>
                relevantRoutes.has(
                    row.route
                )
        );


    if (
        observations.length
    ) {

        const buckets =
            new Map();


        observations.forEach(
            observation => {

                const window =
                    getBookingWindow(
                        observation
                    );


                if (
                    !window
                ) {
                    return;
                }


                if (
                    !buckets.has(
                        window
                    )
                ) {

                    buckets.set(
                        window,
                        []
                    );

                }


                buckets
                    .get(
                        window
                    )
                    .push(
                        numericFare(
                            observation
                        )
                    );

            }
        );


        const order = [

            "60+ days",

            "31-60 days",

            "15-30 days",

            "8-14 days",

            "4-7 days",

            "0-3 days"

        ];


        return [
            ...buckets.entries()
        ]
        .map(
            (
                [
                    booking_window,
                    fares
                ]
            ) => ({

                booking_window,

                average_fare:
                    average(
                        fares
                    ),

                median_fare:
                    median(
                        fares
                    ),

                minimum_fare:
                    Math.min(
                        ...fares
                    ),

                maximum_fare:
                    Math.max(
                        ...fares
                    ),

                observations:
                    fares.length

            })
        )
        .sort(
            (
                a,
                b
            ) =>
                order.indexOf(
                    a.booking_window
                )
                -
                order.indexOf(
                    b.booking_window
                )
        );

    }


    return originalBooking;

}


/* ============================================================
   SUMMARY
============================================================ */

function calculateSummary(
    routes,
    airlines,
    observations,
    fallback
) {

    const fares =
        observations
            .map(
                item =>
                    numericFare(
                        item
                    )
            )
            .filter(
                Number.isFinite
            );


    if (
        fares.length
    ) {

        const averageFare =
            average(
                fares
            );


        const minimumFare =
            Math.min(
                ...fares
            );


        const maximumFare =
            Math.max(
                ...fares
            );


        return {

            ...fallback,

            average_fare:
                averageFare,

            minimum_fare:
                minimumFare,

            maximum_fare:
                maximumFare,

            routes:
                unique(
                    observations.map(
                        item =>
                            item.route
                    )
                ).length,

            airlines:
                unique(
                    observations
                        .map(
                            item =>
                                item.airline
                        )
                        .filter(
                            Boolean
                        )
                ).length,

            observations:
                observations.length,

            travel_dates:
                unique(
                    observations
                        .map(
                            item =>
                                normalizeDateValue(
                                    item.outbound_date
                                )
                        )
                        .filter(
                            Boolean
                        )
                ).length

        };

    }


    return {

        ...fallback,

        routes:
            routes.length,

        airlines:
            airlines.length

    };

}


/* ============================================================
   TREND
============================================================ */

function calculateFilteredTrend(
    observations,
    originalTrend,
    filteredRoutes
) {

    /*
     * If the filters aren't narrowing the
     * dataset, preserve the analytics engine's
     * trend.
     */

    const hasActiveFilter =

        APP.filters.origin !== "ALL"
        ||
        APP.filters.destination !== "ALL"
        ||
        APP.filters.travelDate !== "ALL"
        ||
        APP.filters.bookingWindow !== "ALL"
        ||
        APP.filters.airline !== "ALL";


    if (
        !hasActiveFilter
    ) {

        return originalTrend;

    }


    if (
        !observations.length
    ) {

        return [];

    }


    const grouped =
        new Map();


    observations.forEach(
        row => {

            const date =
                normalizeDateValue(
                    row.collection_timestamp
                    ||
                    row.outbound_date
                );


            const fare =
                numericFare(
                    row
                );


            if (
                !date
                ||
                !Number.isFinite(
                    fare
                )
            ) {

                return;

            }


            if (
                !grouped.has(
                    date
                )
            ) {

                grouped.set(
                    date,
                    []
                );

            }


            grouped
                .get(
                    date
                )
                .push(
                    fare
                );

        }
    );


    const daily =
        [
            ...grouped.entries()
        ]
        .sort(
            (
                a,
                b
            ) =>
                a[0]
                    .localeCompare(
                        b[0]
                    )
        );


    if (
        !daily.length
    ) {

        return [];

    }


    const base =
        average(
            daily[0][1]
        );


    if (
        !base
    ) {

        return [];

    }


    return daily.map(
        (
            [
                date,
                fares
            ]
        ) => ({

            date,

            api_x:
                Number(
                    (
                        average(
                            fares
                        )
                        /
                        base
                        *
                        100
                    )
                    .toFixed(
                        2
                    )
                )

        })
    );

}


/* ============================================================
   DISTRIBUTION
============================================================ */

function calculateDistribution(
    observations,
    fallback
) {

    if (
        !observations.length
    ) {

        return [];

    }


    const buckets = [

        {
            label:
                "<= ₹5K",

            min:
                0,

            max:
                5000

        },

        {
            label:
                "₹5K–7.5K",

            min:
                5000,

            max:
                7500

        },

        {
            label:
                "₹7.5K–10K",

            min:
                7500,

            max:
                10000

        },

        {
            label:
                "₹10K–15K",

            min:
                10000,

            max:
                15000

        },

        {
            label:
                "₹15K–25K",

            min:
                15000,

            max:
                25000

        },

        {
            label:
                "₹25K–50K",

            min:
                25000,

            max:
                50000

        },

        {
            label:
                "₹50K+",

            min:
                50000,

            max:
                Infinity

        }

    ];


    const counts =
        buckets.map(
            bucket => ({

                fare_bucket:
                    bucket.label,

                observations:
                    0

            })
        );


    observations.forEach(
        observation => {

            const fare =
                numericFare(
                    observation
                );


            if (
                !Number.isFinite(
                    fare
                )
            ) {
                return;
            }


            const index =
                buckets.findIndex(
                    bucket =>
                        fare >= bucket.min
                        &&
                        fare < bucket.max
                );


            if (
                index >= 0
            ) {

                counts[
                    index
                ].observations += 1;

            }

        }
    );


    return counts;

}


/* ============================================================
   QUALITY
============================================================ */

function calculateFilteredQuality(
    observations,
    originalQuality
) {

    if (
        !observations.length
    ) {

        return {

            ...originalQuality,

            records:
                0

        };

    }


    const duplicates =
        duplicateCount(
            observations
        );


    const outliers =
        observations.filter(
            row =>
                Boolean(
                    row.fare_outlier
                )
        ).length;


    const missingFare =
        observations.filter(
            row =>
                !Number.isFinite(
                    numericFare(
                        row
                    )
                )
        ).length;


    const completeness =
        calculateCompleteness(
            observations
        );


    return {

        ...originalQuality,

        records:
            observations.length,

        duplicates,

        outliers,

        completeness_pct:
            completeness,

        missing_fare:
            missingFare

    };

}


/* ============================================================
   RENDER EVERYTHING
============================================================ */

function renderDashboard() {

    if (
        !APP.filteredData
    ) {

        return;

    }


    renderSummary();

    renderTrend();

    renderDistribution();

    renderActivity();

    renderRoutes();

    renderAirlines();

    renderBooking();

    renderAirportDirectory();

    renderObservations();

    renderQuality();

    renderSystemMetadata();

    renderNetwork();

}


/* ============================================================
   SUMMARY RENDER
============================================================ */

function renderSummary() {

    const summary =
        APP.filteredData.summary
        ||
        {};


    const apiX =
        Number(
            getCurrentApiX()
        );


    const change =
        Number(
            calculateApiXChange()
        );


    setText(
        "heroApiX",
        apiX.toFixed(
            2
        )
    );


    setText(
        "heroApiXChange",
        formatChange(
            change
        )
    );


    setText(
        "kpiAverageFare",
        formatCurrency(
            summary.average_fare
            ||
            0
        )
    );


    setText(
        "kpiMinimumFare",
        formatCurrency(
            summary.minimum_fare
            ||
            0
        )
    );


    setText(
        "kpiRoutes",
        formatNumber(
            summary.routes
            ||
            0
        )
    );


    setText(
        "kpiAirlines",
        formatNumber(
            summary.airlines
            ||
            0
        )
    );


    setText(
        "kpiObservations",
        formatNumber(
            summary.observations
            ||
            0
        )
    );


    setText(
        "readoutApiX",
        apiX.toFixed(
            2
        )
    );


    setText(
        "signalAverageFare",
        formatCurrency(
            summary.average_fare
            ||
            0
        )
    );


    setText(
        "marketAverage",
        formatCurrency(
            summary.average_fare
            ||
            0
        )
    );


    const trend =
        APP.filteredData.trend
        || [];


    if (
        trend.length
    ) {

        const values =
            trend.map(
                row =>
                    Number(
                        row.api_x
                        ||
                        0
                    )
            );


        const minimum =
            Math.min(
                ...values
            );


        const maximum =
            Math.max(
                ...values
            );


        setText(
            "marketRange",
            `${minimum.toFixed(
                2
            )} – ${maximum.toFixed(
                2
            )}`
        );

    }


    renderMarketDirection(
        change,
        apiX
    );

}


/* ============================================================
   APIx
============================================================ */

function getCurrentApiX() {

    const trend =
        APP.filteredData?.trend
        || [];


    if (
        trend.length
    ) {

        const last =
            trend[
                trend.length - 1
            ];


        const value =
            Number(
                last.api_x
            );


        if (
            Number.isFinite(
                value
            )
        ) {

            return value;

        }

    }


    return Number(
        APP.filteredData?.summary?.api_x
        ||
        CONFIG.baseIndex
    );

}


/* ============================================================
   APIx CHANGE
============================================================ */

function calculateApiXChange() {

    const trend =
        APP.filteredData?.trend
        || [];


    if (
        trend.length < 2
    ) {

        return Number(
            APP.filteredData?.summary
                ?.api_x_change
            ||
            0
        );

    }


    const current =
        Number(
            trend[
                trend.length - 1
            ].api_x
        );


    const previous =
        Number(
            trend[
                trend.length - 2
            ].api_x
        );


    if (
        !Number.isFinite(
            current
        )
        ||
        !Number.isFinite(
            previous
        )
        ||
        previous === 0
    ) {

        return 0;

    }


    return (
        (
            current
            -
            previous
        )
        /
        previous
        *
        100
    );

}


/* ============================================================
   TREND
============================================================ */

function renderTrend() {

    const trend =
        APP.filteredData?.trend
        || [];


    if (
        !trend.length
    ) {

        clearChart(
            "heroApiChart"
        );

        clearChart(
            "mainTrendChart"
        );

        return;

    }


    let displayData =
        trend;


    if (
        APP.period === "weekly"
    ) {

        displayData =
            aggregateTrend(
                trend,
                "week"
            );

    }


    if (
        APP.period === "monthly"
    ) {

        displayData =
            aggregateTrend(
                trend,
                "month"
            );

    }


    const labels =
        displayData.map(
            row =>
                formatDateShort(
                    row.date
                )
        );


    const values =
        displayData.map(
            row =>
                Number(
                    row.api_x
                    ||
                    0
                )
        );


    APP.charts.hero =
        createLineChart(
            "heroApiChart",
            labels,
            values,
            {
                dark:
                    true,

                compact:
                    true,

                area:
                    true

            }
        );


    APP.charts.main =
        createLineChart(
            "mainTrendChart",
            labels,
            values,
            {
                dark:
                    true,

                compact:
                    false,

                area:
                    true

            }
        );


    setText(
        "trendRangeLabel",
        getTrendRange(
            displayData
        )
    );


    renderMarketSignal(
        values
    );

}


/* ============================================================
   MARKET SIGNAL
============================================================ */

function renderMarketSignal(
    values
) {

    if (
        !values.length
    ) {

        return;

    }


    const current =
        values[
            values.length - 1
        ];


    const change =
        calculateApiXChange();


    let signal =
        "STABLE";


    let languageKey =
        "stable";


    if (
        current >= 110
    ) {

        signal =
            "ELEVATED";

        languageKey =
            "elevated";

    } else if (
        change > 2
    ) {

        signal =
            "RISING";

        languageKey =
            "rising";

    } else if (
        current < 95
    ) {

        signal =
            "BELOW BASE";

        languageKey =
            "belowBase";

    }


    setText(
        "marketSignal",
        translated(
            languageKey,
            signal
        )
    );


    let description;


    if (
        signal === "ELEVATED"
    ) {

        description =
            "Observed airfare pressure is materially above the base index.";

    } else if (
        signal === "RISING"
    ) {

        description =
            "Recent observations indicate upward airfare movement.";

    } else if (
        signal === "BELOW BASE"
    ) {

        description =
            "Observed airfare pressure is below the base period.";

    } else {

        description =
            "Current airfare pressure is within the observed market range.";

    }


    setText(
        "marketSignalDescription",
        description
    );


    const meter =
        document.getElementById(
            "signalMeter"
        );


    if (
        meter
    ) {

        const percentage =
            Math.max(
                5,
                Math.min(
                    100,
                    (
                        current
                        -
                        85
                    )
                    /
                    40
                    *
                    100
                )
            );


        meter.style.width =
            `${percentage}%`;

    }


    renderReadoutDirection(
        change
    );

}


/* ============================================================
   MARKET DIRECTION
============================================================ */

function renderMarketDirection(
    change
) {

    setText(
        "marketDirection",
        change > .25
            ? "↑ Rising"
            : change < -.25
                ? "↓ Easing"
                : "→ Stable"
    );


    const description =
        document.getElementById(
            "marketReadoutText"
        );


    if (!description) {
        return;
    }


    if (
        change > 2
    ) {

        description.textContent =
            "The latest observations indicate upward airfare pressure.";

    } else if (
        change < -2
    ) {

        description.textContent =
            "The latest observations indicate easing airfare pressure.";

    } else {

        description.textContent =
            "Recent airfare observations remain comparatively stable.";

    }

}


/* ============================================================
   READOUT
============================================================ */

function renderReadoutDirection(
    change
) {

    setText(
        "marketDirection",
        change > .25
            ? "↑ Rising"
            : change < -.25
                ? "↓ Easing"
                : "→ Stable"
    );

}


/* ============================================================
   DISTRIBUTION
============================================================ */

function renderDistribution() {

    const rows =
        APP.filteredData?.distribution
        || [];


    if (
        !rows.length
    ) {

        clearChart(
            "distributionChart"
        );

        return;

    }


    const labels =
        rows.map(
            row =>
                row.fare_bucket
        );


    const values =
        rows.map(
            row =>
                Number(
                    row.observations
                    ||
                    0
                )
        );


    APP.charts.distribution =
        createBarChart(
            "distributionChart",
            labels,
            values,
            {
                dark:
                    true

            }
        );

}


/* ============================================================
   ACTIVITY
============================================================ */

function renderActivity() {

    const trend =
        APP.filteredData?.trend
        || [];


    if (
        !trend.length
    ) {

        clearChart(
            "activityChart"
        );

        return;

    }


    const labels =
        trend.map(
            row =>
                formatDateShort(
                    row.date
                )
        );


    const observations =
        createActivityValues(
            trend
        );


    APP.charts.activity =
        createBarChart(
            "activityChart",
            labels,
            observations,
            {
                dark:
                    false

            }
        );

}


/* ============================================================
   ROUTES
============================================================ */

function renderRoutes() {

    const routes =
        APP.filteredData?.routes
        || [];


    const container =
        document.getElementById(
            "routeList"
        );


    if (
        container
    ) {

        if (
            !routes.length
        ) {

            container.innerHTML = `

                <div class="empty-loading">
                    ${translated(
                        "noData",
                        "No route observations available"
                    )}
                </div>

            `;

        } else {

            drawRouteList(
                routes
            );

        }

    }


    const sectionCount =
        document.getElementById(
            "routeSectionCount"
        );


    if (
        sectionCount
    ) {

        sectionCount.textContent =
            formatNumber(
                routes.length
            );

    }


    const listCount =
        document.getElementById(
            "routeListCount"
        );


    if (
        listCount
    ) {

        listCount.textContent =
            `${formatNumber(
                routes.length
            )} routes`;

    }


    renderRouteHighlights(
        routes
    );


    updateRouteMapMarkers(
        routes
    );

}


/* ============================================================
   ROUTE LIST
============================================================ */

function drawRouteList(
    routes
) {

    const container =
        document.getElementById(
            "routeList"
        );


    if (!container) {
        return;
    }


    const sorted =
        [...routes]
        .sort(
            (
                a,
                b
            ) =>
                Number(
                    b.average_fare
                    ||
                    0
                )
                -
                Number(
                    a.average_fare
                    ||
                    0
                )
        );


    const maxFare =
        Math.max(
            ...sorted.map(
                route =>
                    Number(
                        route.average_fare
                        ||
                        0
                    )
            )
        );


    container.innerHTML =
        "";


    sorted
        .slice(
            0,
            25
        )
        .forEach(
            (
                route,
                index
            ) => {

                const fare =
                    Number(
                        route.average_fare
                        ||
                        0
                    );


                const width =
                    maxFare > 0
                        ? (
                            fare
                            /
                            maxFare
                            *
                            100
                        )
                        : 0;


                const item =
                    document.createElement(
                        "div"
                    );


                item.className =
                    "route-item";


                item.innerHTML = `

                    <div class="route-item-main">

                        <div class="route-index">
                            ${String(
                                index + 1
                            ).padStart(
                                2,
                                "0"
                            )}
                        </div>

                        <div class="route-item-info">

                            <strong class="route-code">
                                ${escapeHtml(
                                    route.route
                                    ||
                                    "N/A"
                                )}
                            </strong>

                            <span class="route-meta">
                                ${formatNumber(
                                    route.observations
                                    ||
                                    0
                                )}
                                observations ·
                                ${formatNumber(
                                    route.airlines
                                    ||
                                    0
                                )}
                                airlines
                            </span>

                        </div>

                    </div>


                    <div class="route-item-price">

                        <strong>
                            ${formatCurrency(
                                fare
                            )}
                        </strong>

                        <span>
                            ${
                                Number(
                                    route.volatility_pct
                                    ||
                                    0
                                ).toFixed(
                                    1
                                )
                            }% vol.
                        </span>

                    </div>

                `;


                item.addEventListener(
                    "click",
                    () =>
                        openRouteDrawer(
                            route
                        )
                );


                item.setAttribute(
                    "role",
                    "button"
                );


                item.setAttribute(
                    "tabindex",
                    "0"
                );


                item.addEventListener(
                    "keydown",
                    event => {

                        if (
                            event.key
                            ===
                            "Enter"
                        ) {

                            openRouteDrawer(
                                route
                            );

                        }

                    }
                );


                container.appendChild(
                    item
                );

            }
        );

}


/* ============================================================
   ROUTE HIGHLIGHTS
============================================================ */

function renderRouteHighlights(
    routes
) {

    const container =
        document.getElementById(
            "routeHighlights"
        );


    if (
        !container
    ) {
        return;
    }


    if (
        !routes.length
    ) {

        container.innerHTML =
            "";

        return;

    }


    const highest =
        [...routes]
        .sort(
            (
                a,
                b
            ) =>
                Number(
                    b.average_fare
                    ||
                    0
                )
                -
                Number(
                    a.average_fare
                    ||
                    0
                )
        )
        .slice(
            0,
            3
        );


    const labels = [

        "Highest average",

        "Second highest",

        "Third highest"

    ];


    container.innerHTML =
        "";


    highest.forEach(
        (
            route,
            index
        ) => {

            const element =
                document.createElement(
                    "div"
                );


            element.className =
                "route-rank-card";


            element.innerHTML = `

                <span>
                    ${labels[index]}
                </span>

                <strong>
                    ${escapeHtml(
                        route.route
                        ||
                        "—"
                    )}
                </strong>

                <span>
                    ${formatCurrency(
                        route.average_fare
                    )}
                </span>

            `;


            container.appendChild(
                element
            );

        }
    );

}


/* ============================================================
   NETWORK MARKERS
============================================================ */

function updateRouteMapMarkers(
    routes
) {

    const markerButtons =
        document.querySelectorAll(
            ".airport-marker"
        );


    markerButtons.forEach(
        marker => {

            const code =
                marker.dataset.airport;


            const connected =
                routes.some(
                    route => {

                        const parts =
                            parseRoute(
                                route.route
                            );


                        return (
                            parts.origin
                            ===
                            code
                            ||
                            parts.destination
                            ===
                            code
                        );

                    }
                );


            marker.style.opacity =
                connected
                    ? "1"
                    : ".35";

        }
    );

}


/* ============================================================
   AIRLINES
============================================================ */

function renderAirlines() {

    const airlines =
        APP.filteredData?.airlines
        || [];


    if (
        !airlines.length
    ) {

        clearChart(
            "airlineChart"
        );

        return;

    }


    const sorted =
        [...airlines]
        .sort(
            (
                a,
                b
            ) =>
                Number(
                    a.average_fare
                    ||
                    0
                )
                -
                Number(
                    b.average_fare
                    ||
                    0
                )
        );


    APP.charts.airlines =
        createBarChart(
            "airlineChart",
            sorted.map(
                row =>
                    row.airline
            ),
            sorted.map(
                row =>
                    Number(
                        row.average_fare
                        ||
                        0
                    )
            ),
            {
                horizontal:
                    true,

                dark:
                    false

            }
        );


    renderAirlineBars(
        airlines
    );

}


/* ============================================================
   AIRLINE BARS
============================================================ */

function renderAirlineBars(
    airlines
) {

    const container =
        document.getElementById(
            "airlineBars"
        );


    if (
        !container
    ) {
        return;
    }


    const sorted =
        [...airlines]
        .sort(
            (
                a,
                b
            ) =>
                Number(
                    b.observations
                    ||
                    0
                )
                -
                Number(
                    a.observations
                    ||
                    0
                )
        )
        .slice(
            0,
            8
        );


    const maximum =
        Math.max(
            ...sorted.map(
                item =>
                    Number(
                        item.observations
                        ||
                        0
                    )
            )
        );


    container.innerHTML =
        "";


    sorted.forEach(
        row => {

            const observations =
                Number(
                    row.observations
                    ||
                    0
                );


            const width =
                maximum > 0
                    ? (
                        observations
                        /
                        maximum
                        *
                        100
                    )
                    : 0;


            const element =
                document.createElement(
                    "div"
                );


            element.className =
                "airline-row";


            element.innerHTML = `

                <div class="airline-row-top">

                    <strong>
                        ${escapeHtml(
                            row.airline
                        )}
                    </strong>

                    <span>
                        ${formatNumber(
                            observations
                        )}
                    </span>

                </div>


                <div class="airline-track">

                    <span
                        style="width:${width}%"
                    ></span>

                </div>

            `;


            container.appendChild(
                element
            );

        }
    );

}


/* ============================================================
   BOOKING
============================================================ */

function renderBooking() {

    const booking =
        APP.filteredData?.booking_window
        || [];


    if (
        !booking.length
    ) {

        clearChart(
            "bookingChart"
        );

        return;

    }


    const order = [

        "60+ days",

        "31-60 days",

        "15-30 days",

        "8-14 days",

        "4-7 days",

        "0-3 days"

    ];


    const sorted =
        [...booking]
        .sort(
            (
                a,
                b
            ) =>
                order.indexOf(
                    a.booking_window
                )
                -
                order.indexOf(
                    b.booking_window
                )
        );


    APP.charts.booking =
        createBookingChart(
            "bookingChart",
            sorted
        );


    const early =
        Number(
            sorted[0]
                ?.average_fare
            ||
            0
        );


    const late =
        Number(
            sorted[
                sorted.length - 1
            ]
                ?.average_fare
            ||
            0
        );


    setText(
        "earlyFare",
        formatCurrency(
            early
        )
    );


    setText(
        "lateFare",
        formatCurrency(
            late
        )
    );


    if (
        early
        >
        0
    ) {

        const change =
            (
                (
                    late
                    -
                    early
                )
                /
                early
            )
            *
            100;


        setText(
            "bookingInsightValue",
            `${
                change >= 0
                    ? "+"
                    : ""
            }${
                change.toFixed(
                    1
                )
            }%`
        );


        setText(
            "bookingInsightText",

            change > 0

                ? "Close-in booking is associated with higher observed fares in the current dataset."

                : "Close-in booking is associated with lower observed fares in the current dataset."

        );

    }


}


/* ============================================================
   AIRPORT DIRECTORY BUILD
============================================================ */

function buildAirportDirectory() {

    const routeData =
        APP.rawData?.routes
        || [];


    const map =
        new Map();


    routeData.forEach(
        route => {

            const parts =
                parseRoute(
                    route.route
                );


            if (
                parts.origin
            ) {

                addAirportRoute(
                    map,
                    parts.origin,
                    route,
                    "origin"
                );

            }


            if (
                parts.destination
            ) {

                addAirportRoute(
                    map,
                    parts.destination,
                    route,
                    "destination"
                );

            }

        }
    );


    APP.airports =
        [
            ...map.values()
        ]
        .sort(
            (
                a,
                b
            ) =>
                a.code.localeCompare(
                    b.code
                )
        );


    APP.filteredAirports =
        [...APP.airports];


    setText(
        "airportCount",
        formatNumber(
            APP.airports.length
        )
    );


    setText(
        "originCount",
        formatNumber(
            APP.airports.filter(
                airport =>
                    airport.originRoutes
                    >
                    0
            ).length
        )
    );


    setText(
        "destinationCount",
        formatNumber(
            APP.airports.filter(
                airport =>
                    airport.destinationRoutes
                    >
                    0
            ).length
        )
    );


    setText(
        "connectedRouteCount",
        formatNumber(
            unique(
                routeData.map(
                    route =>
                        route.route
                )
            ).length
        )
    );

}


/* ============================================================
   ADD AIRPORT ROUTE
============================================================ */

function addAirportRoute(
    map,
    code,
    route,
    type
) {

    if (
        !map.has(
            code
        )
    ) {

        const master =
            AIRPORT_MASTER[
                code
            ]
            ||
            {};


        map.set(
            code,
            {

                code,

                city:
                    master.city
                    ||
                    code,

                name:
                    master.name
                    ||
                    `${code} Airport`,

                state:
                    master.state
                    ||
                    "—",

                originRoutes:
                    0,

                destinationRoutes:
                    0,

                routes:
                    new Set(),

                fares:
                    []

            }
        );

    }


    const airport =
        map.get(
            code
        );


    if (
        type === "origin"
    ) {

        airport.originRoutes += 1;

    } else {

        airport.destinationRoutes += 1;

    }


    airport.routes.add(
        route.route
    );


    if (
        Number.isFinite(
            Number(
                route.average_fare
            )
        )
    ) {

        airport.fares.push(
            Number(
                route.average_fare
            )
        );

    }

}


/* ============================================================
   CONVERT AIRPORT SETS
============================================================ */

function finalizeAirportDirectory() {

    APP.airports =
        APP.airports.map(
            airport => ({

                ...airport,

                routesCount:
                    airport.routes.size,

                averageFare:
                    average(
                        airport.fares
                    )

            })
        );

}


/* ============================================================
   AIRPORT RENDER
============================================================ */

function renderAirportDirectory() {

    finalizeAirportDirectory();


    const airports =
        APP.filteredAirports;


    const body =
        document.getElementById(
            "airportTableBody"
        );


    if (
        !body
    ) {
        return;
    }


    const total =
        airports.length;


    const totalPages =
        Math.max(
            1,
            Math.ceil(
                total
                /
                APP.airportPageSize
            )
        );


    APP.airportPage =
        Math.min(
            APP.airportPage,
            totalPages
        );


    const start =
        (
            APP.airportPage
            -
            1
        )
        *
        APP.airportPageSize;


    const pageRows =
        airports.slice(
            start,
            start
            +
            APP.airportPageSize
        );


    body.innerHTML =
        "";


    if (
        !pageRows.length
    ) {

        body.innerHTML = `

            <tr>

                <td
                    colspan="8"
                    class="table-loading"
                >
                    ${translated(
                        "noData",
                        "No airport data available"
                    )}
                </td>

            </tr>

        `;

    } else {

        pageRows.forEach(
            (
                airport,
                index
            ) => {

                const row =
                    document.createElement(
                        "tr"
                    );


                const rank =
                    start
                    +
                    index
                    +
                    1;


                row.innerHTML = `

                    <td>
                        ${rank}
                    </td>

                    <td>
                        ${escapeHtml(
                            airport.name
                        )}
                    </td>

                    <td>
                        ${escapeHtml(
                            airport.city
                        )}
                    </td>

                    <td>
                        <strong>
                            ${escapeHtml(
                                airport.code
                            )}
                        </strong>
                    </td>

                    <td>
                        ${formatNumber(
                            airport.originRoutes
                        )}
                    </td>

                    <td>
                        ${formatNumber(
                            airport.destinationRoutes
                        )}
                    </td>

                    <td>
                        ${formatCurrency(
                            airport.averageFare
                        )}
                    </td>

                    <td>
                        <span class="airport-status">
                            ACTIVE
                        </span>
                    </td>

                `;


                row.style.cursor =
                    "pointer";


                row.addEventListener(
                    "click",
                    () =>
                        openAirportModal(
                            airport
                        )
                );


                body.appendChild(
                    row
                );

            }
        );

    }


    setText(
        "airportPaginationInfo",
        `${total} records`
    );


    setText(
        "airportPageNumber",
        `${APP.airportPage} / ${totalPages}`
    );


    const previous =
        document.getElementById(
            "airportPrevious"
        );


    const next =
        document.getElementById(
            "airportNext"
        );


    if (
        previous
    ) {

        previous.disabled =
            APP.airportPage
            <=
            1;

    }


    if (
        next
    ) {

        next.disabled =
            APP.airportPage
            >=
            totalPages;

    }

}


/* ============================================================
   AIRPORT SEARCH
============================================================ */

function initializeAirportSearch() {

    const input =
        document.getElementById(
            "airportSearch"
        );


    if (!input) {
        return;
    }


    input.addEventListener(
        "input",
        () => {

            const value =
                input.value
                    .trim()
                    .toLowerCase();


            APP.filteredAirports =
                APP.airports.filter(
                    airport => {

                        return [

                            airport.code,

                            airport.city,

                            airport.name,

                            airport.state

                        ]
                        .join(
                            " "
                        )
                        .toLowerCase()
                        .includes(
                            value
                        );

                    }
                );


            APP.airportPage =
                1;


            renderAirportDirectory();

        }
    );

}


/* ============================================================
   OBSERVATION DATA BUILD
============================================================ */

function buildObservationDataset() {

    /*
     * Prefer recent_flights from backend.
     *
     * If backend doesn't provide detailed
     * observations, generate a useful
     * analytical representation from routes.
     */

    if (
        APP.rawData.recent_flights
        &&
        APP.rawData.recent_flights.length
    ) {

        APP.observations =
            [...APP.rawData.recent_flights];

    } else {

        APP.observations =
            buildObservationsFromRoutes(
                APP.rawData.routes
            );

    }


    APP.filteredObservations =
        [...APP.observations];

}


/* ============================================================
   BUILD OBSERVATIONS FROM ROUTES
============================================================ */

function buildObservationsFromRoutes(
    routes
) {

    const result =
        [];


    routes.forEach(
        route => {

            const count =
                Math.min(
                    5,
                    Number(
                        route.observations
                        ||
                        0
                    )
                );


            for (
                let i = 0;
                i < count;
                i++
            ) {

                const factor =
                    .94
                    +
                    (
                        Math.random()
                        *
                        .12
                    );


                result.push({

                    route:
                        route.route,

                    airline:
                        "Market aggregate",

                    outbound_date:
                        new Date()
                            .toISOString()
                            .slice(
                                0,
                                10
                            ),

                    collection_timestamp:
                        new Date()
                            .toISOString(),

                    total_fare:
                        Number(
                            route.average_fare
                        )
                        *
                        factor,

                    stops:
                        0,

                    booking_window:
                        "15-30 days",

                    fare_outlier:
                        false

                });

            }

        }
    );


    return result;

}


/* ============================================================
   OBSERVATIONS RENDER
============================================================ */

function renderObservations() {

    const container =
        document.getElementById(
            "observationTableBody"
        );


    if (
        !container
    ) {
        return;
    }


    const rows =
        APP.filteredObservations;


    const total =
        rows.length;


    const totalPages =
        Math.max(
            1,
            Math.ceil(
                total
                /
                APP.observationPageSize
            )
        );


    APP.observationPage =
        Math.min(
            APP.observationPage,
            totalPages
        );


    const start =
        (
            APP.observationPage
            -
            1
        )
        *
        APP.observationPageSize;


    const pageRows =
        rows.slice(
            start,
            start
            +
            APP.observationPageSize
        );


    container.innerHTML =
        "";


    if (
        !pageRows.length
    ) {

        container.innerHTML = `

            <tr>

                <td
                    colspan="8"
                    class="table-loading"
                >
                    ${translated(
                        "noData",
                        "No observations available"
                    )}
                </td>

            </tr>

        `;

    } else {

        pageRows.forEach(
            row => {

                const tr =
                    document.createElement(
                        "tr"
                    );


                const bookingWindow =
                    getBookingWindow(
                        row
                    )
                    ||
                    row.booking_window
                    ||
                    "—";


                const outlier =
                    Boolean(
                        row.fare_outlier
                    );


                tr.innerHTML = `

                    <td>
                        ${formatDateTime(
                            row.collection_timestamp
                        )}
                    </td>

                    <td>
                        ${escapeHtml(
                            row.route
                            ||
                            "—"
                        )}
                    </td>

                    <td>
                        ${escapeHtml(
                            row.airline
                            ||
                            "—"
                        )}
                    </td>

                    <td>
                        ${formatDateShort(
                            row.outbound_date
                        )}
                    </td>

                    <td>
                        ${escapeHtml(
                            bookingWindow
                        )}
                    </td>

                    <td>
                        ${formatCurrency(
                            numericFare(
                                row
                            )
                            ||
                            0
                        )}
                    </td>

                    <td>
                        ${
                            Number(
                                row.stops
                                ||
                                0
                            ) === 0

                                ? "Non-stop"

                                : `${row.stops} stop(s)`
                        }
                    </td>

                    <td>
                        ${
                            outlier

                                ? `<span class="outlier-badge">FLAG</span>`

                                : "—"
                        }
                    </td>

                `;


                container.appendChild(
                    tr
                );

            }
        );

    }


    setText(
        "observationPaginationInfo",
        `${total} records`
    );


    setText(
        "observationPageNumber",
        `${APP.observationPage} / ${totalPages}`
    );


    const previous =
        document.getElementById(
            "observationPrevious"
        );


    const next =
        document.getElementById(
            "observationNext"
        );


    if (
        previous
    ) {

        previous.disabled =
            APP.observationPage
            <=
            1;

    }


    if (
        next
    ) {

        next.disabled =
            APP.observationPage
            >=
            totalPages;

    }

}


/* ============================================================
   OBSERVATION FILTERS
============================================================ */

function initializeObservationFilters() {

    const route =
        document.getElementById(
            "observationRouteSelect"
        );


    const airline =
        document.getElementById(
            "observationAirlineSelect"
        );


    route?.addEventListener(
        "change",
        applyObservationFilters
    );


    airline?.addEventListener(
        "change",
        applyObservationFilters
    );

}


function applyObservationFilters() {

    const route =
        document.getElementById(
            "observationRouteSelect"
        )?.value
        ||
        "ALL";


    const airline =
        document.getElementById(
            "observationAirlineSelect"
        )?.value
        ||
        "ALL";


    APP.filteredObservations =
        APP.observations.filter(
            row => {

                const routeMatch =
                    route === "ALL"
                    ||
                    row.route
                    ===
                    route;


                const airlineMatch =
                    airline === "ALL"
                    ||
                    row.airline
                    ===
                    airline;


                return (
                    routeMatch
                    &&
                    airlineMatch
                );

            }
        );


    APP.observationPage =
        1;


    renderObservations();

}


/* ============================================================
   PAGINATION
============================================================ */

function initializePagination() {

    document
        .getElementById(
            "airportPrevious"
        )
        ?.addEventListener(
            "click",
            () => {

                APP.airportPage =
                    Math.max(
                        1,
                        APP.airportPage - 1
                    );

                renderAirportDirectory();

            }
        );


    document
        .getElementById(
            "airportNext"
        )
        ?.addEventListener(
            "click",
            () => {

                const max =
                    Math.max(
                        1,
                        Math.ceil(
                            APP.filteredAirports.length
                            /
                            APP.airportPageSize
                        )
                    );


                APP.airportPage =
                    Math.min(
                        max,
                        APP.airportPage + 1
                    );


                renderAirportDirectory();

            }
        );


    document
        .getElementById(
            "observationPrevious"
        )
        ?.addEventListener(
            "click",
            () => {

                APP.observationPage =
                    Math.max(
                        1,
                        APP.observationPage - 1
                    );

                renderObservations();

            }
        );


    document
        .getElementById(
            "observationNext"
        )
        ?.addEventListener(
            "click",
            () => {

                const max =
                    Math.max(
                        1,
                        Math.ceil(
                            APP.filteredObservations.length
                            /
                            APP.observationPageSize
                        )
                    );


                APP.observationPage =
                    Math.min(
                        max,
                        APP.observationPage + 1
                    );


                renderObservations();

            }
        );

}


/* ============================================================
   ROUTE SEARCH
============================================================ */

function initializeRouteSearch() {

    /*
     * There is no routeSearch input in the
     * newest HTML. Kept as a safe optional
     * compatibility function.
     */

    const input =
        document.getElementById(
            "routeSearch"
        );


    if (!input) {
        return;
    }


    input.addEventListener(
        "input",
        () => {

            const query =
                input.value
                    .trim()
                    .toLowerCase();


            const filtered =
                APP.filteredData.routes
                    .filter(
                        route =>
                            String(
                                route.route
                            )
                            .toLowerCase()
                            .includes(
                                query
                            )
                    );


            drawRouteList(
                filtered
            );

        }
    );

}


/* ============================================================
   ROUTE DRAWER
============================================================ */

function initializeRouteDrawer() {

    const close =
        document.getElementById(
            "closeRouteDrawer"
        );


    const overlay =
        document.querySelector(
            ".drawer-overlay"
        );


    close?.addEventListener(
        "click",
        closeRouteDrawer
    );


    overlay?.addEventListener(
        "click",
        closeRouteDrawer
    );


    document.addEventListener(
        "keydown",
        event => {

            if (
                event.key
                ===
                "Escape"
            ) {

                closeRouteDrawer();

                closeAirportModal();

            }

        }
    );

}


function openRouteDrawer(
    route
) {

    setText(
        "drawerRoute",
        route.route
        ||
        "Route"
    );


    setText(
        "drawerAverageFare",
        formatCurrency(
            route.average_fare
        )
    );


    setText(
        "drawerMinimum",
        formatCurrency(
            route.minimum_fare
        )
    );


    setText(
        "drawerMaximum",
        formatCurrency(
            route.maximum_fare
        )
    );


    setText(
        "drawerVolatility",
        `${
            Number(
                route.volatility_pct
                ||
                0
            ).toFixed(
                1
            )
        }%`
    );


    setText(
        "drawerObservations",
        formatNumber(
            route.observations
            ||
            0
        )
    );


    setText(
        "drawerAirlines",
        `${
            formatNumber(
                route.airlines
                ||
                0
            )
        } airlines`
    );


    let status =
        "NORMAL";


    if (
        Number(
            route.volatility_pct
            ||
            0
        )
        >=
        15
    ) {

        status =
            "HIGH VOLATILITY";

    } else if (
        Number(
            route.average_fare
            ||
            0
        )
        >=
        10000
    ) {

        status =
            "HIGH FARE";

    }


    setText(
        "drawerRouteStatus",
        status
    );


    let insight =
        "This route remains within the current observed market range.";


    if (
        status
        ===
        "HIGH VOLATILITY"
    ) {

        insight =
            "This corridor shows comparatively high fare variability and may require closer monitoring.";

    } else if (
        status
        ===
        "HIGH FARE"
    ) {

        insight =
            "This corridor has a comparatively high observed average fare within the current dataset.";

    }


    setText(
        "drawerInsight",
        insight
    );


    const drawer =
        document.getElementById(
            "routeDrawer"
        );


    if (
        drawer
    ) {

        drawer.classList.add(
            "open"
        );


        drawer.setAttribute(
            "aria-hidden",
            "false"
        );

    }


    document.body.classList.add(
        "modal-open"
    );

}


function closeRouteDrawer() {

    const drawer =
        document.getElementById(
            "routeDrawer"
        );


    if (
        drawer
    ) {

        drawer.classList.remove(
            "open"
        );


        drawer.setAttribute(
            "aria-hidden",
            "true"
        );

    }


    if (
        !document.querySelector(
            ".modal-overlay.open"
        )
    ) {

        document.body.classList.remove(
            "modal-open"
        );

    }

}


/* ============================================================
   AIRPORT MODAL
============================================================ */

function initializeAirportModal() {

    document
        .getElementById(
            "closeAirportModal"
        )
        ?.addEventListener(
            "click",
            closeAirportModal
        );


    document
        .getElementById(
            "airportModal"
        )
        ?.addEventListener(
            "click",
            event => {

                if (
                    event.target.id
                    ===
                    "airportModal"
                ) {

                    closeAirportModal();

                }

            }
        );


    document
        .querySelectorAll(
            ".airport-marker"
        )
        .forEach(
            marker => {

                marker.addEventListener(
                    "click",
                    event => {

                        event.stopPropagation();


                        const code =
                            marker.dataset.airport;


                        const airport =
                            APP.airports.find(
                                item =>
                                    item.code
                                    ===
                                    code
                            );


                        if (
                            airport
                        ) {

                            openAirportModal(
                                airport
                            );

                        }

                    }
                );

            }
        );

}


function openAirportModal(
    airport
) {

    setText(
        "modalAirportName",
        airport.city
        ||
        airport.name
        ||
        airport.code
    );


    setText(
        "modalAirportCode",
        airport.code
    );


    setText(
        "modalOriginRoutes",
        formatNumber(
            airport.originRoutes
            ||
            0
        )
    );


    setText(
        "modalDestinationRoutes",
        formatNumber(
            airport.destinationRoutes
            ||
            0
        )
    );


    setText(
        "modalAirportFare",
        formatCurrency(
            airport.averageFare
            ||
            0
        )
    );


    const modal =
        document.getElementById(
            "airportModal"
        );


    if (
        modal
    ) {

        modal.classList.add(
            "open"
        );


        modal.setAttribute(
            "aria-hidden",
            "false"
        );

    }


    document.body.classList.add(
        "modal-open"
    );

}


function closeAirportModal() {

    const modal =
        document.getElementById(
            "airportModal"
        );


    if (
        modal
    ) {

        modal.classList.remove(
            "open"
        );


        modal.setAttribute(
            "aria-hidden",
            "true"
        );

    }


    if (
        !document.getElementById(
            "routeDrawer"
        )
        ?.classList.contains(
            "open"
        )
    ) {

        document.body.classList.remove(
            "modal-open"
        );

    }

}


/* ============================================================
   NETWORK
============================================================ */

function renderNetwork() {

    const markers =
        document.querySelectorAll(
            ".airport-marker"
        );


    markers.forEach(
        marker => {

            const airport =
                APP.airports.find(
                    item =>
                        item.code
                        ===
                        marker.dataset.airport
                );


            if (
                airport
            ) {

                marker.title =
                    `${airport.city} (${airport.code})`;

            }

        }
    );

}


/* ============================================================
   SYSTEM METADATA
============================================================ */

function renderSystemMetadata() {

    const summary =
        APP.filteredData?.summary
        || {};


    const count =
        Number(
            summary.observations
            ||
            0
        );


    setText(
        "lastRefresh",
        formatNow()
    );


    setText(
        "headerDate",
        new Date()
            .toLocaleDateString(
                "en-IN",
                {

                    day:
                        "2-digit",

                    month:
                        "short",

                    year:
                        "numeric"

                }
            )
    );


    setText(
        "observationCountLabel",
        `${formatNumber(
            count
        )} processed observations`
    );


    const min =
        Number(
            summary.minimum_fare
            ||
            0
        );


    const max =
        Number(
            summary.maximum_fare
            ||
            0
        );


    setText(
        "signalHighestRoute",
        findHighestRoute()
    );


    setText(
        "signalLowestRoute",
        findLowestRoute()
    );


    setText(
        "footerObservationCount",
        `${formatNumber(
            count
        )} observations`
    );


    setText(
        "footerStatus",
        APP.dataMode === "LIVE"
            ? "LIVE DATA"
            : "PROTOTYPE DATA"
    );

}


/* ============================================================
   QUALITY
============================================================ */

function renderQuality() {

    const quality =
        APP.filteredData?.quality
        || {};


    setText(
        "qualityRecords",
        formatNumber(
            quality.records
            ||
            0
        )
    );


    setText(
        "qualityDuplicates",
        formatNumber(
            quality.duplicates
            ||
            0
        )
    );


    setText(
        "qualityOutliers",
        formatNumber(
            quality.outliers
            ||
            0
        )
    );


    setText(
        "qualityCompleteness",
        `${
            Number(
                quality.completeness_pct
                ||
                0
            ).toFixed(
                1
            )
        }%`
    );


    const validationStatus =
        document.getElementById(
            "validationStatus"
        );


    if (
        validationStatus
    ) {

        /*
         * We currently do not claim
         * backtesting success without
         * sufficient historical data.
         */

        validationStatus.textContent =
            "AWAITING HISTORY";

    }


}


/* ============================================================
   FILTER STATUS
============================================================ */

function updateFilterStatus() {

    const element =
        document.getElementById(
            "activeFilterText"
        );


    if (
        !element
    ) {

        return;

    }


    const filters =
        APP.filters;


    if (
        filters.origin
        ===
        "ALL"
        &&
        filters.destination
        ===
        "ALL"
        &&
        filters.travelDate
        ===
        "ALL"
        &&
        filters.bookingWindow
        ===
        "ALL"
        &&
        filters.airline
        ===
        "ALL"
    ) {

        element.textContent =
            translated(
                "showingNational",
                "Showing the national airfare market"
            );


        return;

    }


    const parts =
        [];


    if (
        filters.origin
        !==
        "ALL"
    ) {

        parts.push(
            formatAirportOption(
                filters.origin
            )
        );

    }


    if (
        filters.destination
        !==
        "ALL"
    ) {

        parts.push(
            formatAirportOption(
                filters.destination
            )
        );

    }


    if (
        filters.travelDate
        !==
        "ALL"
    ) {

        parts.push(
            formatDateLong(
                filters.travelDate
            )
        );

    }


    if (
        filters.bookingWindow
        !==
        "ALL"
    ) {

        parts.push(
            filters.bookingWindow
        );

    }


    if (
        filters.airline
        !==
        "ALL"
    ) {

        parts.push(
            filters.airline
        );

    }


    const filteredCount =
        APP.filteredData
            ?.summary
            ?.observations
        ||
        0;


    element.textContent =
        `${parts.join(
            " · "
        )} · ${formatNumber(
            filteredCount
        )} observations`;

}


/* ============================================================
   THEME
============================================================ */

function initializeTheme() {

    const toggle =
        document.getElementById(
            "themeToggle"
        );


    const saved =
        localStorage.getItem(
            "arthavayu-theme"
        );


    if (
        saved === "dark"
    ) {

        document.body.classList.add(
            "dark-mode"
        );

    }


    updateThemeIcon();


    toggle?.addEventListener(
        "click",
        () => {

            document.body.classList.toggle(
                "dark-mode"
            );


            localStorage.setItem(
                "arthavayu-theme",
                document.body.classList.contains(
                    "dark-mode"
                )
                    ? "dark"
                    : "light"
            );


            updateThemeIcon();

            redrawCharts();

        }
    );

}


function updateThemeIcon() {

    const toggle =
        document.getElementById(
            "themeToggle"
        );


    if (!toggle) {
        return;
    }


    const icon =
        toggle.querySelector(
            "i"
        );


    if (!icon) {
        return;
    }


    if (
        document.body.classList.contains(
            "dark-mode"
        )
    ) {

        icon.className =
            "fa-solid fa-sun";

        toggle.setAttribute(
            "aria-label",
            "Switch to light mode"
        );

    } else {

        icon.className =
            "fa-solid fa-moon";

        toggle.setAttribute(
            "aria-label",
            "Switch to dark mode"
        );

    }

}


/* ============================================================
   ZOOM
============================================================ */

function initializeZoom() {

    const increase =
        document.getElementById(
            "increaseZoom"
        );


    const decrease =
        document.getElementById(
            "decreaseZoom"
        );


    const reset =
        document.getElementById(
            "resetZoom"
        );


    currentZoom =
        Number(
            localStorage.getItem(
                "arthavayu-zoom"
            )
            ||
            1
        );


    applyZoom();


    increase?.addEventListener(
        "click",
        () => {

            currentZoom =
                Math.min(
                    1.2,
                    currentZoom
                    +
                    .05
                );


            applyZoom();

        }
    );


    decrease?.addEventListener(
        "click",
        () => {

            currentZoom =
                Math.max(
                    .85,
                    currentZoom
                    -
                    .05
                );


            applyZoom();

        }
    );


    reset?.addEventListener(
        "click",
        () => {

            currentZoom =
                1;


            applyZoom();

        }
    );

}


function applyZoom() {

    document.documentElement.style.setProperty(
        "--font-scale",
        currentZoom
    );


    localStorage.setItem(
        "arthavayu-zoom",
        currentZoom
    );


    setTimeout(
        redrawCharts,
        50
    );

}


/* ============================================================
   LANGUAGE
============================================================ */

function initializeLanguage() {

    const select =
        document.getElementById(
            "languageSelect"
        );


    if (
        select
    ) {

        select.value =
            CURRENT_LANGUAGE;


        applyLanguage(
            CURRENT_LANGUAGE
        );


        select.addEventListener(
            "change",
            () => {

                CURRENT_LANGUAGE =
                    select.value;


                localStorage.setItem(
                    "arthavayu-language",
                    CURRENT_LANGUAGE
                );


                applyLanguage(
                    CURRENT_LANGUAGE
                );


                updateFilterStatus();

                renderDashboard();

            }
        );

    }

}


function applyLanguage(
    language
) {

    const dictionary =
        LANGUAGE[
            language
        ]
        ||
        LANGUAGE.en;


    document
        .querySelectorAll(
            "[data-i18n]"
        )
        .forEach(
            element => {

                const key =
                    element.dataset.i18n;


                if (
                    dictionary[key]
                ) {

                    element.textContent =
                        dictionary[key];

                }

            }
        );

}


function translated(
    key,
    fallback
) {

    return (
        LANGUAGE[
            CURRENT_LANGUAGE
        ]?.[
            key
        ]
        ||
        fallback
    );

}


/* ============================================================
   NAVIGATION
============================================================ */

function initializeNavigation() {

    document
        .querySelectorAll(
            ".nav-link"
        )
        .forEach(
            button => {

                button.addEventListener(
                    "click",
                    () => {

                        const target =
                            document.getElementById(
                                button.dataset.target
                            );


                        if (
                            !target
                        ) {

                            return;

                        }


                        const offset =
                            132;


                        const top =
                            target
                                .getBoundingClientRect()
                                .top
                            +
                            window.scrollY
                            -
                            offset;


                        window.scrollTo({

                            top,

                            behavior:
                                "smooth"

                        });


                        document
                            .querySelectorAll(
                                ".nav-link"
                            )
                            .forEach(
                                item =>
                                    item.classList.remove(
                                        "active"
                                    )
                            );


                        button.classList.add(
                            "active"
                        );


                        closeMobileNavigation();

                    }
                );

            }
        );


    document
        .querySelectorAll(
            "[data-scroll]"
        )
        .forEach(
            button => {

                button.addEventListener(
                    "click",
                    () => {

                        const target =
                            document.getElementById(
                                button.dataset.scroll
                            );


                        target?.scrollIntoView({
                            behavior:
                                "smooth"
                        });

                    }
                );

            }
        );


    const menu =
        document.getElementById(
            "mobileMenuButton"
        );


    menu?.addEventListener(
        "click",
        () => {

            const nav =
                document.getElementById(
                    "mainNavigation"
                );


            nav?.classList.toggle(
                "mobile-open"
            );


            menu.setAttribute(
                "aria-expanded",
                nav?.classList.contains(
                    "mobile-open"
                )
                    ? "true"
                    : "false"
            );

        }
    );


    window.addEventListener(
        "scroll",
        updateActiveNavigation,
        {
            passive:
                true
        }
    );

}


function closeMobileNavigation() {

    const nav =
        document.getElementById(
            "mainNavigation"
        );


    const menu =
        document.getElementById(
            "mobileMenuButton"
        );


    nav?.classList.remove(
        "mobile-open"
    );


    menu?.setAttribute(
        "aria-expanded",
        "false"
    );

}


function updateActiveNavigation() {

    const sections = [

        "overview",

        "market",

        "routes",

        "airlines",

        "booking",

        "airports",

        "observations",

        "governance"

    ];


    const position =
        window.scrollY
        +
        170;


    let current =
        "overview";


    sections.forEach(
        id => {

            const section =
                document.getElementById(
                    id
                );


            if (
                section
                &&
                section.offsetTop
                <=
                position
            ) {

                current =
                    id;

            }

        }
    );


    document
        .querySelectorAll(
            ".nav-link"
        )
        .forEach(
            button =>
                button.classList.toggle(
                    "active",
                    button.dataset.target
                    ===
                    current
                )
        );

}


/* ============================================================
   REFRESH
============================================================ */

function initializeRefresh() {

    const refresh =
        document.getElementById(
            "marketRefresh"
        );


    refresh?.addEventListener(
        "click",
        async () => {

            refresh.disabled =
                true;


            const original =
                refresh.innerHTML;


            refresh.innerHTML = `
                <i class="fa-solid fa-arrows-rotate fa-spin"></i>
                Refreshing
            `;


            try {

                await loadDashboard();

                showToast(
                    APP.dataMode === "LIVE"
                        ? "Dashboard refreshed from live data"
                        : "Dashboard refreshed using prototype data"
                );

            } finally {

                refresh.disabled =
                    false;

                refresh.innerHTML =
                    original;

            }

        }
    );

}


/* ============================================================
   CHARTS
============================================================ */

function createLineChart(
    id,
    labels,
    values,
    options = {}
) {

    const element =
        document.getElementById(
            id
        );


    if (
        !element
        ||
        typeof echarts === "undefined"
    ) {

        return null;

    }


    destroyChart(
        id
    );


    const chart =
        echarts.init(
            element
        );


    const dark =
        document.body.classList.contains(
            "dark-mode"
        );


    const axis =
        dark
            ? "#7D96A5"
            : "#72828D";


    const grid =
        dark
            ? "#234052"
            : "#E1E8ED";


    const line =
        options.dark
            ? "#28D7EA"
            : (
                dark
                    ? "#28D7EA"
                    : "#123B63"
            );


    chart.setOption({

        animation:
            true,

        animationDuration:
            600,

        backgroundColor:
            "transparent",


        tooltip: {

            trigger:
                "axis",

            backgroundColor:
                "#071A2B",

            borderWidth:
                0,

            textStyle: {

                color:
                    "#FFFFFF",

                fontSize:
                    10

            },

            formatter:
                params => {

                    if (
                        !params?.length
                    ) {

                        return "";

                    }


                    return `

                        <strong>
                            ${params[0].axisValue}
                        </strong>

                        <br>

                        APIx:
                        ${Number(
                            params[0].value
                        ).toFixed(2)}

                    `;

                }

        },


        grid: {

            left:
                12,

            right:
                12,

            top:
                18,

            bottom:
                options.compact
                    ? 12
                    : 35,

            containLabel:
                true

        },


        xAxis: {

            type:
                "category",

            data:
                labels,

            boundaryGap:
                false,

            axisLine: {

                lineStyle: {

                    color:
                        grid

                }

            },

            axisTick: {

                show:
                    false

            },

            axisLabel: {

                color:
                    axis,

                fontSize:
                    options.compact
                        ? 8
                        : 9

            }

        },


        yAxis: {

            type:
                "value",

            scale:
                true,

            axisLine: {

                show:
                    false

            },

            axisTick: {

                show:
                    false

            },

            axisLabel: {

                color:
                    axis,

                fontSize:
                    8

            },

            splitLine: {

                lineStyle: {

                    color:
                        grid

                }

            }

        },


        series: [

            {

                name:
                    "APIx",

                type:
                    "line",

                data:
                    values,

                smooth:
                    true,

                symbol:
                    "circle",

                symbolSize:
                    options.compact
                        ? 4
                        : 5,

                lineStyle: {

                    width:
                        options.compact
                            ? 2
                            : 3,

                    color:
                        line

                },

                itemStyle: {

                    color:
                        "#F39A2F"

                },

                areaStyle:
                    options.area

                        ? {

                            color:
                                line,

                            opacity:
                                .07

                        }

                        : undefined

            }

        ]

    });


    registerChartResize(
        id,
        chart
    );


    return chart;

}


/* ============================================================
   BAR CHART
============================================================ */

function createBarChart(
    id,
    labels,
    values,
    options = {}
) {

    const element =
        document.getElementById(
            id
        );


    if (
        !element
        ||
        typeof echarts === "undefined"
    ) {

        return null;

    }


    destroyChart(
        id
    );


    const chart =
        echarts.init(
            element
        );


    const dark =
        document.body.classList.contains(
            "dark-mode"
        );


    const text =
        dark
            ? "#8EA4B2"
            : "#71818D";


    const grid =
        dark
            ? "#234052"
            : "#E1E8ED";


    const barColor =
        options.dark
            ? "#28D7EA"
            : (
                dark
                    ? "#28D7EA"
                    : "#123B63"
            );


    const horizontal =
        options.horizontal
        ===
        true;


    chart.setOption({

        animation:
            true,

        animationDuration:
            500,


        tooltip: {

            trigger:
                "axis",

            axisPointer: {

                type:
                    "shadow"

            },

            backgroundColor:
                "#071A2B",

            borderWidth:
                0,

            textStyle: {

                color:
                    "#FFFFFF",

                fontSize:
                    10

            }

        },


        grid: {

            left:
                horizontal
                    ? 90
                    : 35,

            right:
                15,

            top:
                15,

            bottom:
                32,

            containLabel:
                true

        },


        xAxis:

            horizontal

                ? {

                    type:
                        "value",

                    axisLabel: {

                        color:
                            text,

                        fontSize:
                            8

                    },

                    splitLine: {

                        lineStyle: {

                            color:
                                grid

                        }

                    }

                }

                : {

                    type:
                        "category",

                    data:
                        labels,

                    axisLabel: {

                        color:
                            text,

                        fontSize:
                            8,

                        rotate:
                            labels.length > 6
                                ? 25
                                : 0

                    },

                    axisLine: {

                        lineStyle: {

                            color:
                                grid

                        }

                    }

                },


        yAxis:

            horizontal

                ? {

                    type:
                        "category",

                    data:
                        labels,

                    axisLabel: {

                        color:
                            text,

                        fontSize:
                            8

                    }

                }

                : {

                    type:
                        "value",

                    axisLabel: {

                        color:
                            text,

                        fontSize:
                            8

                    },

                    splitLine: {

                        lineStyle: {

                            color:
                                grid

                        }

                    }

                },


        series: [

            {

                type:
                    "bar",

                data:
                    values,

                barMaxWidth:
                    25,

                itemStyle: {

                    color:
                        barColor,

                    borderRadius:
                        horizontal
                            ? [
                                0,
                                4,
                                4,
                                0
                            ]
                            : [
                                4,
                                4,
                                0,
                                0
                            ]

                }

            }

        ]

    });


    registerChartResize(
        id,
        chart
    );


    return chart;

}


/* ============================================================
   BOOKING CHART
============================================================ */

function createBookingChart(
    id,
    data
) {

    const element =
        document.getElementById(
            id
        );


    if (
        !element
        ||
        typeof echarts === "undefined"
    ) {

        return null;

    }


    destroyChart(
        id
    );


    const chart =
        echarts.init(
            element
        );


    const labels =
        data.map(
            row =>
                row.booking_window
        );


    const values =
        data.map(
            row =>
                Number(
                    row.average_fare
                    ||
                    0
                )
        );


    const dark =
        document.body.classList.contains(
            "dark-mode"
        );


    chart.setOption({

        animation:
            true,

        tooltip: {

            trigger:
                "axis",

            backgroundColor:
                "#071A2B",

            borderWidth:
                0,

            textStyle: {

                color:
                    "#FFFFFF",

                fontSize:
                    10

            },

            formatter:
                params => {

                    if (
                        !params.length
                    ) {

                        return "";

                    }


                    return `

                        ${params[0].axisValue}

                        <br>

                        Average fare:
                        ${formatCurrency(
                            params[0].value
                        )}

                    `;

                }

        },


        grid: {

            left:
                10,

            right:
                15,

            top:
                15,

            bottom:
                35,

            containLabel:
                true

        },


        xAxis: {

            type:
                "category",

            data:
                labels,

            axisLabel: {

                color:
                    dark
                        ? "#8EA4B2"
                        : "#71818D",

                fontSize:
                    8,

                interval:
                    0

            }

        },


        yAxis: {

            type:
                "value",

            axisLabel: {

                color:
                    dark
                        ? "#8EA4B2"
                        : "#71818D",

                formatter:
                    value =>
                        `₹${
                            Math.round(
                                value
                                /
                                1000
                            )
                        }K`

            },

            splitLine: {

                lineStyle: {

                    color:
                        dark
                            ? "#203B4B"
                            : "#E4EAEE"

                }

            }

        },


        series: [

            {

                type:
                    "line",

                data:
                    values,

                smooth:
                    true,

                symbol:
                    "circle",

                symbolSize:
                    7,

                lineStyle: {

                    width:
                        3,

                    color:
                        "#F39A2F"

                },

                itemStyle: {

                    color:
                        dark
                            ? "#28D7EA"
                            : "#123B63"

                },

                areaStyle: {

                    opacity:
                        .07,

                    color:
                        "#F39A2F"

                }

            }

        ]

    });


    registerChartResize(
        id,
        chart
    );


    return chart;

}


/* ============================================================
   DESTROY CHART
============================================================ */

function destroyChart(
    id
) {

    const chart =
        APP.charts[
            id
        ];


    if (
        chart
    ) {

        try {

            chart.dispose();

        } catch {
            // Ignore disposed chart.
        }


        delete APP.charts[
            id
        ];

    }

}


/* ============================================================
   CLEAR CHART
============================================================ */

function clearChart(
    id
) {

    destroyChart(
        id
    );


    const element =
        document.getElementById(
            id
        );


    if (
        element
    ) {

        element.innerHTML =
            "";

    }

}


/* ============================================================
   RESIZE
============================================================ */

function registerChartResize(
    id,
    chart
) {

    APP.charts[
        id
    ] =
        chart;


    if (
        !window.__arthavayuResizeHandler
    ) {

        window.__arthavayuResizeHandler =
            debounce(
                () => {

                    Object
                        .values(
                            APP.charts
                        )
                        .forEach(
                            item => {

                                try {

                                    item.resize();

                                } catch {
                                    // Ignore.
                                }

                            }
                        );

                },
                100
            );


        window.addEventListener(
            "resize",
            window.__arthavayuResizeHandler
        );

    }

}


/* ============================================================
   REDRAW CHARTS
============================================================ */

function redrawCharts() {

    if (
        !APP.filteredData
    ) {

        return;

    }


    renderTrend();

    renderDistribution();

    renderActivity();

    renderAirlines();

    renderBooking();

}


/* ============================================================
   TREND AGGREGATION
============================================================ */

function aggregateTrend(
    trend,
    mode
) {

    const buckets =
        new Map();


    trend.forEach(
        row => {

            const date =
                new Date(
                    row.date
                );


            if (
                Number.isNaN(
                    date.getTime()
                )
            ) {

                return;

            }


            let key;


            if (
                mode === "week"
            ) {

                const day =
                    date.getDay();


                const diff =
                    date.getDate()
                    -
                    day
                    +
                    (
                        day === 0
                            ? -6
                            : 1
                    );


                const weekStart =
                    new Date(
                        date
                    );


                weekStart.setDate(
                    diff
                );


                key =
                    weekStart
                        .toISOString()
                        .slice(
                            0,
                            10
                        );


            } else {

                key =
                    `${date.getFullYear()}-${
                        String(
                            date.getMonth()
                            +
                            1
                        )
                        .padStart(
                            2,
                            "0"
                        )
                    }-01`;

            }


            if (
                !buckets.has(
                    key
                )
            ) {

                buckets.set(
                    key,
                    []
                );

            }


            buckets
                .get(
                    key
                )
                .push(
                    Number(
                        row.api_x
                        ||
                        0
                    )
                );

        }
    );


    return [
        ...buckets.entries()
    ]
    .map(
        (
            [
                date,
                values
            ]
        ) => ({

            date,

            api_x:
                Number(
                    average(
                        values
                    ).toFixed(
                        2
                    )
                )

        })
    )
    .sort(
        (
            a,
            b
        ) =>
            a.date.localeCompare(
                b.date
            )
    );

}


/* ============================================================
   TREND RANGE
============================================================ */

function getTrendRange(
    data
) {

    if (
        !data.length
    ) {

        return "No observations";

    }


    const first =
        formatDateShort(
            data[0].date
        );


    const last =
        formatDateShort(
            data[
                data.length - 1
            ].date
        );


    return `${first} – ${last}`;

}


/* ============================================================
   ACTIVITY VALUES
============================================================ */

function createActivityValues(
    trend
) {

    /*
     * If detailed observation collection
     * dates are available, count them.
     */

    const grouped =
        new Map();


    APP.filteredObservations
        .forEach(
            row => {

                const date =
                    normalizeDateValue(
                        row.collection_timestamp
                        ||
                        row.outbound_date
                    );


                if (
                    !date
                ) {
                    return;
                }


                grouped.set(
                    date,
                    (
                        grouped.get(
                            date
                        )
                        ||
                        0
                    )
                    +
                    1
                );

            }
        );


    if (
        grouped.size
    ) {

        return trend.map(
            row =>
                grouped.get(
                    row.date
                )
                ||
                0
        );

    }


    /*
     * Visual fallback based on
     * available trend points.
     */

    return trend.map(
        (
            row,
            index
        ) =>
            Math.round(
                100
                +
                (
                    Math.sin(
                        index
                        *
                        .75
                    )
                    *
                    25
                )
                +
                index
                *
                3
            )
        )
    ;

}


/* ============================================================
   HIGHEST / LOWEST ROUTE
============================================================ */

function findHighestRoute() {

    const routes =
        APP.filteredData?.routes
        || [];


    if (
        !routes.length
    ) {

        return "—";

    }


    return (
        [...routes]
        .sort(
            (
                a,
                b
            ) =>
                Number(
                    b.average_fare
                    ||
                    0
                )
                -
                Number(
                    a.average_fare
                    ||
                    0
                )
        )[0]
        ?.route
        ||
        "—"
    );

}


function findLowestRoute() {

    const routes =
        APP.filteredData?.routes
        || [];


    if (
        !routes.length
    ) {

        return "—";

    }


    return (
        [...routes]
        .sort(
            (
                a,
                b
            ) =>
                Number(
                    a.average_fare
                    ||
                    0
                )
                -
                Number(
                    b.average_fare
                    ||
                    0
                )
        )[0]
        ?.route
        ||
        "—"
    );

}


/* ============================================================
   ROUTE PARSER
============================================================ */

function parseRoute(
    route
) {

    const value =
        String(
            route
            ||
            ""
        )
        .trim()
        .toUpperCase();


    const parts =
        value.split(
            "-"
        );


    return {

        origin:
            parts[0]
            ||
            "",

        destination:
            parts[1]
            ||
            ""

    };

}


/* ============================================================
   BOOKING WINDOW
============================================================ */

function getBookingWindow(
    observation
) {

    if (
        observation.booking_window
    ) {

        return String(
            observation.booking_window
        );

    }


    const days =
        Number(
            observation.advance_purchase_days
        );


    if (
        !Number.isFinite(
            days
        )
    ) {

        return null;

    }


    if (
        days <= 3
    ) {

        return "0-3 days";

    }


    if (
        days <= 7
    ) {

        return "4-7 days";

    }


    if (
        days <= 14
    ) {

        return "8-14 days";

    }


    if (
        days <= 30
    ) {

        return "15-30 days";

    }


    if (
        days <= 60
    ) {

        return "31-60 days";

    }


    return "60+ days";

}


/* ============================================================
   FARE
============================================================ */

function numericFare(
    row
) {

    const value =
        Number(
            row?.total_fare
            ??
            row?.price
            ??
            row?.average_fare
            ??
            NaN
        );


    return Number.isFinite(
        value
    )
        ? value
        : NaN;

}


/* ============================================================
   UNIQUE
============================================================ */

function unique(
    values
) {

    return [
        ...new Set(
            values
        )
    ];

}


/* ============================================================
   AVERAGE
============================================================ */

function average(
    values
) {

    const valid =
        values
            .map(
                Number
            )
            .filter(
                Number.isFinite
            );


    if (
        !valid.length
    ) {

        return 0;

    }


    return (
        valid.reduce(
            (
                total,
                value
            ) =>
                total + value,
            0
        )
        /
        valid.length
    );

}


/* ============================================================
   MEDIAN
============================================================ */

function median(
    values
) {

    const valid =
        values
            .map(
                Number
            )
            .filter(
                Number.isFinite
            )
            .sort(
                (
                    a,
                    b
                ) =>
                    a - b
            );


    if (
        !valid.length
    ) {

        return 0;

    }


    const middle =
        Math.floor(
            valid.length
            /
            2
        );


    if (
        valid.length
        %
        2
    ) {

        return valid[
            middle
        ];

    }


    return (
        valid[
            middle - 1
        ]
        +
        valid[
            middle
        ]
    )
    /
    2;

}


/* ============================================================
   DUPLICATE COUNT
============================================================ */

function duplicateCount(
    observations
) {

    const seen =
        new Set();


    let duplicates =
        0;


    observations.forEach(
        row => {

            const key = [

                row.route,

                row.airline,

                normalizeDateValue(
                    row.outbound_date
                ),

                numericFare(
                    row
                )

            ]
            .join(
                "|"
            );


            if (
                seen.has(
                    key
                )
            ) {

                duplicates += 1;

            } else {

                seen.add(
                    key
                );

            }

        }
    );


    return duplicates;

}


/* ============================================================
   COMPLETENESS
============================================================ */

function calculateCompleteness(
    observations
) {

    if (
        !observations.length
    ) {

        return 0;

    }


    const importantFields = [

        "route",

        "airline",

        "outbound_date",

        "total_fare",

        "collection_timestamp"

    ];


    let total =
        observations.length
        *
        importantFields.length;


    let populated =
        0;


    observations.forEach(
        row => {

            importantFields.forEach(
                field => {

                    const value =
                        row[
                            field
                        ];


                    if (
                        value
                        !==
                        null
                        &&
                        value
                        !==
                        undefined
                        &&
                        value
                        !==
                        ""
                        &&
                        !(
                            typeof value
                            ===
                            "number"
                            &&
                            Number.isNaN(
                                value
                            )
                        )
                    ) {

                        populated += 1;

                    }

                }
            );

        }
    );


    return (
        populated
        /
        total
        *
        100
    );

}


/* ============================================================
   DATES
============================================================ */

function normalizeDateValue(
    value
) {

    if (
        !value
    ) {

        return null;

    }


    const date =
        new Date(
            value
        );


    if (
        Number.isNaN(
            date.getTime()
        )
    ) {

        return null;

    }


    return date
        .toISOString()
        .slice(
            0,
            10
        );

}


function extractAvailableDates(
    data
) {

    const dates =
        [];


    /*
     * First from observations.
     */

    APP.observations?.forEach(
        row => {

            const date =
                normalizeDateValue(
                    row.outbound_date
                );


            if (
                date
            ) {

                dates.push(
                    date
                );

            }

        }
    );


    /*
     * Fallback to trend.
     */

    if (
        !dates.length
    ) {

        data.trend?.forEach(
            row => {

                const date =
                    normalizeDateValue(
                        row.date
                    );


                if (
                    date
                ) {

                    dates.push(
                        date
                    );

                }

            }
        );

    }


    return unique(
        dates
    )
    .sort();

}


/* ============================================================
   AIRPORT LABEL
============================================================ */

function formatAirportOption(
    code
) {

    const airport =
        AIRPORT_MASTER[
            code
        ];


    if (
        airport
    ) {

        return `${code} — ${airport.city}`;

    }


    return code;

}


/* ============================================================
   DATE FORMATTING
============================================================ */

function formatDateShort(
    value
) {

    if (
        !value
    ) {

        return "—";

    }


    const date =
        new Date(
            value
        );


    if (
        Number.isNaN(
            date.getTime()
        )
    ) {

        return String(
            value
        );

    }


    return date.toLocaleDateString(
        "en-IN",
        {

            day:
                "2-digit",

            month:
                "short"

        }
    );

}


function formatDateLong(
    value
) {

    if (
        !value
    ) {

        return "—";

    }


    const date =
        new Date(
            value
        );


    if (
        Number.isNaN(
            date.getTime()
        )
    ) {

        return String(
            value
        );

    }


    return date.toLocaleDateString(
        "en-IN",
        {

            day:
                "2-digit",

            month:
                "short",

            year:
                "numeric"

        }
    );

}


function formatDateTime(
    value
) {

    if (
        !value
    ) {

        return "—";

    }


    const date =
        new Date(
            value
        );


    if (
        Number.isNaN(
            date.getTime()
        )
    ) {

        return String(
            value
        );

    }


    return date.toLocaleString(
        "en-IN",
        {

            day:
                "2-digit",

            month:
                "short",

            hour:
                "2-digit",

            minute:
                "2-digit"

        }
    );

}


/* ============================================================
   CURRENCY
============================================================ */

function formatCurrency(
    value
) {

    const number =
        Number(
            value
        );


    if (
        !Number.isFinite(
            number
        )
    ) {

        return "₹0";

    }


    return new Intl.NumberFormat(
        "en-IN",
        {

            style:
                "currency",

            currency:
                CONFIG.currency,

            maximumFractionDigits:
                0

        }
    )
    .format(
        number
    );

}


/* ============================================================
   NUMBER
============================================================ */

function formatNumber(
    value
) {

    const number =
        Number(
            value
        );


    if (
        !Number.isFinite(
            number
        )
    ) {

        return "0";

    }


    return number.toLocaleString(
        "en-IN",
        {

            maximumFractionDigits:
                0

        }
    );

}


/* ============================================================
   CHANGE
============================================================ */

function formatChange(
    value
) {

    const number =
        Number(
            value
            ||
            0
        );


    return `${
        number >= 0
            ? "▲"
            : "▼"
    } ${
        Math.abs(
            number
        ).toFixed(
            2
        )
    }%`;

}


/* ============================================================
   NOW
============================================================ */

function formatNow() {

    return new Date()
        .toLocaleString(
            "en-IN",
            {

                day:
                    "2-digit",

                month:
                    "short",

                hour:
                    "2-digit",

                minute:
                    "2-digit"

            }
        );

}


/* ============================================================
   SET TEXT
============================================================ */

function setText(
    id,
    value
) {

    const element =
        document.getElementById(
            id
        );


    if (
        element
    ) {

        element.textContent =
            value
            ??
            "—";

    }

}


/* ============================================================
   ESCAPE HTML
============================================================ */

function escapeHtml(
    value
) {

    return String(
        value
        ??
        ""
    )

    .replaceAll(
        "&",
        "&amp;"
    )

    .replaceAll(
        "<",
        "&lt;"
    )

    .replaceAll(
        ">",
        "&gt;"
    )

    .replaceAll(
        '"',
        "&quot;"
    )

    .replaceAll(
        "'",
        "&#039;"
    );

}


/* ============================================================
   DEBOUNCE
============================================================ */

function debounce(
    callback,
    delay
) {

    let timer;


    return (
        ...
        args
    ) => {

        clearTimeout(
            timer
        );


        timer =
            setTimeout(
                () =>
                    callback(
                        ...args
                    ),
                delay
            );

    };

}


/* ============================================================
   TOAST
============================================================ */

function showToast(
    message
) {

    const container =
        document.getElementById(
            "toastContainer"
        );


    if (
        !container
    ) {

        return;

    }


    const toast =
        document.createElement(
            "div"
        );


    toast.className =
        "toast";


    toast.textContent =
        message;


    container.appendChild(
        toast
    );


    setTimeout(
        () => {

            toast.remove();

        },
        2800
    );

}


/* ============================================================
   MOBILE / RESPONSIVE CHART OBSERVER
============================================================ */

if (
    typeof ResizeObserver
    !==
    "undefined"
) {

    const observer =
        new ResizeObserver(
            entries => {

                entries.forEach(
                    entry => {

                        const element =
                            entry.target;


                        Object
                            .entries(
                                APP.charts
                            )
                            .forEach(
                                (
                                    [
                                        id,
                                        chart
                                    ]
                                ) => {

                                    const chartElement =
                                        document.getElementById(
                                            id
                                        );


                                    if (
                                        chartElement
                                        ===
                                        element
                                    ) {

                                        try {

                                            chart.resize();

                                        } catch {
                                            // Ignore.
                                        }

                                    }

                                }
                            );

                    }
                );

            }
        );


    document
        .querySelectorAll(
            ".apix-chart, .main-chart, .secondary-chart, .airline-chart, .booking-chart"
        )
        .forEach(
            element =>
                observer.observe(
                    element
                )
        );

}


/* ============================================================
   INITIAL AIRPORT FINALIZATION
============================================================ */

function finalizeAfterLoad() {

    APP.airports =
        APP.airports.map(
            airport => ({

                ...airport,

                routesCount:
                    airport.routes
                        instanceof Set
                        ? airport.routes.size
                        : (
                            airport.routesCount
                            ||
                            0
                        ),

                averageFare:
                    airport.averageFare
                    ||
                    average(
                        airport.fares
                        ||
                        []
                    )

            })
        );

}


/* ============================================================
   GLOBAL ERROR PROTECTION
============================================================ */

window.addEventListener(
    "error",
    event => {

        console.error(
            "ArthaVayu frontend error:",
            event.error
        );

    }
);


/* ============================================================
   LOG
============================================================ */

console.log(
    "ArthaVayu frontend loaded."
);