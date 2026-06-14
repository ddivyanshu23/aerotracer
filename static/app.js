// Airport Name Mapping Dictionary
const AIRPORT_NAMES = {
    "DEL": "Delhi (DEL)",
    "BOM": "Mumbai (BOM)",
    "BLR": "Bengaluru (BLR)",
    "HYD": "Hyderabad (HYD)",
    "MAA": "Chennai (MAA)",
    "CCU": "Kolkata (CCU)",
    "GOI": "Goa (GOI)",
    "JAI": "Jaipur (JAI)",
    "AMD": "Ahmedabad (AMD)",
    "PNQ": "Pune (PNQ)",
    "COK": "Cochin (COK)",
    "SXR": "Srinagar (SXR)",
    "IXC": "Chandigarh (IXC)",
    "GAU": "Guwahati (GAU)",
    "PAT": "Patna (PAT)",
    "VNS": "Varanasi (VNS)",
    "IXB": "Bagdogra (IXB)",
    "RPR": "Raipur (RPR)",
    "IDR": "Indore (IDR)",
    "NAG": "Nagpur (NAG)",
    "LKO": "Lucknow (LKO)",
    "IXL": "Leh (IXL)",
    // International
    "BKK": "Bangkok (BKK)",
    "SIN": "Singapore (SIN)",
    "KUL": "Kuala Lumpur (KUL)",
    "HAN": "Hanoi (HAN)",
    "SGN": "Ho Chi Minh City (SGN)",
    "MNL": "Manila (MNL)",
    "CGK": "Jakarta (CGK)",
    "DPS": "Bali (DPS)",
    "DXB": "Dubai (DXB)",
    "DOH": "Doha (DOH)",
    "AUH": "Abu Dhabi (AUH)",
    "MCT": "Muscat (MCT)",
    "BAH": "Bahrain (BAH)",
    "RUH": "Riyadh (RUH)",
    "AMM": "Amman (AMM)",
    "NRT": "Tokyo Narita (NRT)",
    "HND": "Tokyo Haneda (HND)",
    "ICN": "Seoul (ICN)",
    "HKG": "Hong Kong (HKG)",
    "PVG": "Shanghai (PVG)",
    "TPE": "Taipei (TPE)",
    "LHR": "London Heathrow (LHR)",
    "CDG": "Paris Charles de Gaulle (CDG)",
    "FRA": "Frankfurt (FRA)",
    "AMS": "Amsterdam (AMS)",
    "FCO": "Rome (FCO)",
    "BCN": "Barcelona (BCN)",
    "IST": "Istanbul (IST)",
    "VIE": "Vienna (VIE)",
    "ZRH": "Zurich (ZRH)",
    "MUC": "Munich (MUC)",
    "PRG": "Prague (PRG)",
    "BUD": "Budapest (BUD)",
    "WAW": "Warsaw (WAW)",
    "ATH": "Athens (ATH)",
    "JFK": "New York (JFK)",
    "SFO": "San Francisco (SFO)",
    "LAX": "Los Angeles (LAX)",
    "ORD": "Chicago (ORD)",
    "YYZ": "Toronto (YYZ)",
    "EWR": "Newark (EWR)",
    "IAD": "Washington Dulles (IAD)",
    "SYD": "Sydney (SYD)",
    "MEL": "Melbourne (MEL)",
    "AKL": "Auckland (AKL)",
    "BNE": "Brisbane (BNE)",
    "NBO": "Nairobi (NBO)",
    "CPT": "Cape Town (CPT)",
    "CAI": "Cairo (CAI)",
    "ADD": "Addis Ababa (ADD)",
    "CMN": "Casablanca (CMN)",
    "CMB": "Colombo (CMB)",
    "KTM": "Kathmandu (KTM)",
    "DAC": "Dhaka (DAC)",
    "MLE": "Male (MLE)"
};

function getAirportLabel(code) {
    if (!code) return '';
    return AIRPORT_NAMES[code.toUpperCase()] || code.toUpperCase();
}

// Extract just the city part (without the code in parentheses)
function getAirportCity(code) {
    if (!code) return '';
    const label = AIRPORT_NAMES[code.toUpperCase()];
    if (!label) return code.toUpperCase();
    return label.replace(/\s*\(.*?\)\s*$/, '');
}

function resolveAirportInput(text) {
    if (!text) return '';
    const clean = text.trim().toUpperCase();
    
    // If already a 3-letter valid code, return it
    if (clean.length === 3 && AIRPORT_NAMES[clean]) {
        return clean;
    }
    
    // Search exact substring mapping
    for (const [code, desc] of Object.entries(AIRPORT_NAMES)) {
        if (desc.toUpperCase().includes(clean) || code === clean) {
            return code;
        }
    }
    
    // Fuzzy mapping for prefixes/suffixes
    const cleanCity = clean.split('(')[0].trim();
    for (const [code, desc] of Object.entries(AIRPORT_NAMES)) {
        const descCity = desc.split('(')[0].trim().toUpperCase();
        if (descCity.includes(cleanCity) || cleanCity.includes(descCity)) {
            return code;
        }
    }
    
    return clean;
}

// Scored fuzzy search for airport suggestions
function scoreAirportMatch(query, code, label) {
    const q = query.toLowerCase();
    const codeLower = code.toLowerCase();
    const labelLower = label.toLowerCase();
    const cityLower = label.replace(/\s*\(.*?\)\s*$/, '').toLowerCase();
    
    // Exact code match
    if (codeLower === q) return 100;
    // Exact city match
    if (cityLower === q) return 95;
    // Code starts with query
    if (codeLower.startsWith(q)) return 85;
    // City starts with query
    if (cityLower.startsWith(q)) return 80;
    // City word starts with query
    const words = cityLower.split(/\s+/);
    for (const w of words) {
        if (w.startsWith(q)) return 70;
    }
    // City contains query
    if (cityLower.includes(q)) return 50;
    // Label contains query
    if (labelLower.includes(q)) return 30;
    
    return 0;
}

function getAirportSuggestions(query, max = 6) {
    if (!query || query.trim().length === 0) return [];
    const q = query.trim();
    
    const scored = [];
    for (const [code, label] of Object.entries(AIRPORT_NAMES)) {
        const s = scoreAirportMatch(q, code, label);
        if (s > 0) scored.push({ code, label, city: label.replace(/\s*\(.*?\)\s*$/, ''), score: s });
    }
    
    scored.sort((a, b) => b.score - a.score);
    return scored.slice(0, max);
}

function initAirportAutocomplete() {
    const inputs = ['search-origin', 'search-dest', 'alert-origin', 'alert-dest'];
    
    inputs.forEach(id => {
        const input = document.getElementById(id);
        if (!input) return;
        
        const wrapper = input.closest('.airport-field-wrapper');
        if (!wrapper) return;
        
        // Create dropdown container
        const dropdown = document.createElement('div');
        dropdown.className = 'airport-autocomplete';
        dropdown.setAttribute('role', 'listbox');
        wrapper.appendChild(dropdown);
        
        // Create resolved badge below wrapper
        const badge = document.createElement('div');
        badge.className = 'airport-resolved-badge';
        badge.style.display = 'none';
        wrapper.parentElement.appendChild(badge);
        
        let highlightedIdx = -1;
        let currentSuggestions = [];
        
        function renderDropdown(suggestions) {
            currentSuggestions = suggestions;
            highlightedIdx = -1;
            
            if (suggestions.length === 0) {
                dropdown.classList.remove('open');
                dropdown.innerHTML = '';
                return;
            }
            
            dropdown.innerHTML = suggestions.map((s, i) => `
                <button type="button" class="airport-suggestion" data-code="${s.code}" data-index="${i}" role="option">
                    <span class="airport-suggestion__city">${s.city}</span>
                    <span class="airport-suggestion__code">${s.code}</span>
                </button>
            `).join('');
            
            dropdown.classList.add('open');
            
            // Click handler on each suggestion
            dropdown.querySelectorAll('.airport-suggestion').forEach(btn => {
                btn.addEventListener('mousedown', (e) => {
                    e.preventDefault(); // Prevent blur
                    const code = btn.dataset.code;
                    input.value = code;
                    dropdown.classList.remove('open');
                    showResolvedBadge(code);
                });
            });
        }
        
        function showResolvedBadge(code) {
            if (code && AIRPORT_NAMES[code]) {
                const city = getAirportCity(code);
                badge.innerHTML = `✈️ ${city} <span class="code">(${code})</span>`;
                badge.style.display = 'inline-flex';
            } else {
                badge.style.display = 'none';
            }
        }
        
        function highlightSuggestion(idx) {
            const btns = dropdown.querySelectorAll('.airport-suggestion');
            btns.forEach(b => b.classList.remove('highlighted'));
            if (idx >= 0 && idx < btns.length) {
                btns[idx].classList.add('highlighted');
                btns[idx].scrollIntoView({ block: 'nearest' });
            }
            highlightedIdx = idx;
        }
        
        // Input event — live search
        input.addEventListener('input', () => {
            const q = input.value.trim();
            if (q.length === 0) {
                dropdown.classList.remove('open');
                badge.style.display = 'none';
                return;
            }
            const suggestions = getAirportSuggestions(q);
            renderDropdown(suggestions);
        });
        
        // Keyboard navigation
        input.addEventListener('keydown', (e) => {
            if (!dropdown.classList.contains('open')) return;
            
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                highlightSuggestion(Math.min(highlightedIdx + 1, currentSuggestions.length - 1));
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                highlightSuggestion(Math.max(highlightedIdx - 1, 0));
            } else if (e.key === 'Enter') {
                e.preventDefault();
                if (highlightedIdx >= 0 && highlightedIdx < currentSuggestions.length) {
                    const code = currentSuggestions[highlightedIdx].code;
                    input.value = code;
                    dropdown.classList.remove('open');
                    showResolvedBadge(code);
                }
            } else if (e.key === 'Escape') {
                dropdown.classList.remove('open');
            }
        });
        
        // On blur: resolve and show badge
        input.addEventListener('blur', () => {
            setTimeout(() => dropdown.classList.remove('open'), 150);
            const resolved = resolveAirportInput(input.value);
            if (resolved && resolved !== input.value) {
                input.value = resolved;
            }
            showResolvedBadge(resolved);
        });
        
        // On focus: re-trigger if there's text
        input.addEventListener('focus', () => {
            if (input.value.trim().length > 0) {
                const suggestions = getAirportSuggestions(input.value.trim());
                renderDropdown(suggestions);
            }
        });
        
        // Show initial badge for pre-filled values
        const initial = resolveAirportInput(input.value);
        if (initial) showResolvedBadge(initial);
    });
}


// App state
let currentChart = null;
let activeSearchInterval = null;

document.addEventListener('DOMContentLoaded', () => {
    initParticles();
    initTypewriterTerminal();
    initFeatureTabs();
    initSPAViews();
    loadDashboardData();
    initSearchForm();
    initAlerts();
    initAirportAutocomplete();
});

// Feature Showcase Tabs Switching
function initFeatureTabs() {
    const tabBtns = document.querySelectorAll('.feature-tab-btn');
    const panels = document.querySelectorAll('.feature-panel');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            panels.forEach(p => p.classList.remove('active'));

            btn.classList.add('active');
            const target = btn.getAttribute('data-feature');
            const pnl = document.getElementById(`feat-${target}`);
            if (pnl) pnl.classList.add('active');
        });
    });
}

// SPA View Management & Modal Controls
function initSPAViews() {
    const navBtns = document.querySelectorAll('.nav-link-btn');
    const viewLanding = document.getElementById('view-landing');
    const viewWorkspace = document.getElementById('view-workspace');
    const workTabs = document.querySelectorAll('.workspace-tab-content');
    
    // View switching function
    function switchView(viewName) {
        // Toggle Nav active state
        navBtns.forEach(btn => {
            if (btn.getAttribute('data-view') === viewName) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        });
        
        if (viewName === 'landing') {
            viewWorkspace.style.display = 'none';
            viewLanding.classList.add('active');
        } else {
            viewLanding.classList.remove('active');
            viewWorkspace.style.display = 'block';
            
            // Switch active workspace panel
            workTabs.forEach(tab => {
                if (tab.id === `work-${viewName}`) {
                    tab.classList.add('active');
                    tab.style.display = 'block';
                } else {
                    tab.classList.remove('active');
                    tab.style.display = 'none';
                }
            });
            
            // Special initializations on tab open
            if (viewName === 'analytics') {
                loadDashboardData();
            } else if (viewName === 'alerts') {
                loadAlerts();
            }
        }
    }
    
    // Bind Nav Buttons
    navBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            switchView(btn.getAttribute('data-view'));
        });
    });
    
    // Bind Logo to return home
    const logoHome = document.getElementById('logo-home');
    if (logoHome) {
        logoHome.addEventListener('click', () => {
            switchView('landing');
        });
    }
    
    // Hero Actions Links
    const btnHeroLaunch = document.getElementById('btn-hero-launch');
    if (btnHeroLaunch) {
        btnHeroLaunch.addEventListener('click', () => {
            switchView('search');
        });
    }
    
    // Learn More Modal controls
    const btnHeroLearn = document.getElementById('btn-hero-learn');
    const learnMoreModal = document.getElementById('learn-more-modal');
    const btnCloseModal = document.getElementById('btn-close-modal');
    
    if (btnHeroLearn && learnMoreModal) {
        btnHeroLearn.addEventListener('click', () => {
            learnMoreModal.classList.add('active');
        });
    }
    
    if (btnCloseModal && learnMoreModal) {
        btnCloseModal.addEventListener('click', () => {
            learnMoreModal.classList.remove('active');
        });
        
        // Close modal when clicking background
        learnMoreModal.addEventListener('click', (e) => {
            if (e.target === learnMoreModal) {
                learnMoreModal.classList.remove('active');
            }
        });
    }
}

// 3D Canvas Particle Network Background
function initParticles() {
    const canvas = document.getElementById('particle-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    
    let particles = [];
    const maxParticles = 60;
    
    function resize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    
    window.addEventListener('resize', resize);
    resize();
    
    class Particle {
        constructor() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.vx = (Math.random() - 0.5) * 0.4;
            this.vy = (Math.random() - 0.5) * 0.4;
            this.radius = Math.random() * 2 + 1;
        }
        
        update() {
            this.x += this.vx;
            this.y += this.vy;
            
            if (this.x < 0 || this.x > canvas.width) this.vx *= -1;
            if (this.y < 0 || this.y > canvas.height) this.vy *= -1;
        }
        
        draw() {
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
            ctx.fillStyle = 'rgba(0, 212, 255, 0.4)';
            ctx.fill();
        }
    }
    
    for (let i = 0; i < maxParticles; i++) {
        particles.push(new Particle());
    }
    
    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        for (let i = 0; i < particles.length; i++) {
            particles[i].update();
            particles[i].draw();
            
            for (let j = i + 1; j < particles.length; j++) {
                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                
                if (dist < 100) {
                    ctx.beginPath();
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.strokeStyle = `rgba(0, 212, 255, ${0.12 * (1 - dist / 100)})`;
                    ctx.lineWidth = 0.8;
                    ctx.stroke();
                }
            }
        }
        
        requestAnimationFrame(animate);
    }
    
    animate();
}

// Staggered Typewriter Terminal reveal
function initTypewriterTerminal() {
    const term = document.getElementById('hero-terminal-output');
    if (!term) return;
    
    const lines = [
        "> Initializing SkyTracer agent connection...",
        "> Connection established. Database active.",
        "> Starting cron monitor: checking active alerts...",
        "> Scanning LKO → IXL (Leh) via Protobuf client...",
        "> ALERT: Price dropped below threshold for LKO → GOI!",
        "> Saved record #1,208 to local history database.",
        "> Ready for user input... █"
    ];
    
    term.innerHTML = '';
    let currentLine = 0;
    
    function typeNextLine() {
        if (currentLine >= lines.length) return;
        
        const lineText = lines[currentLine];
        const span = document.createElement('span');
        span.className = 'term-line';
        
        if (lineText.includes('established') || lineText.includes('Saved')) {
            span.classList.add('text-emerald');
        } else if (lineText.includes('ALERT')) {
            span.classList.add('text-gold');
        } else if (lineText.includes('Scanning')) {
            span.classList.add('text-cyan');
        }
        
        term.appendChild(span);
        
        let charIndex = 0;
        function typeChar() {
            if (charIndex < lineText.length) {
                span.textContent += lineText.charAt(charIndex);
                charIndex++;
                setTimeout(typeChar, 25);
            } else {
                currentLine++;
                setTimeout(typeNextLine, 600);
            }
        }
        
        typeChar();
    }
    
    typeNextLine();
}

// Formatters
function formatPrice(price) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
        maximumFractionDigits: 0
    }).format(price);
}

function formatDateTime(isoString) {
    if (!isoString) return '--';
    const date = new Date(isoString);
    return date.toLocaleString('en-IN', {
        day: '2-digit',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Load Dashboard Overview Data
async function loadDashboardData() {
    try {
        const response = await fetch('/api/routes');
        const routes = await response.json();
        
        // Update stats card safely
        const routesCountEl = document.getElementById('stat-routes-count');
        if (routesCountEl) routesCountEl.textContent = routes.length;
        
        const priceCountEl = document.getElementById('stats-price-count');
        if (priceCountEl) {
            let totalRecords = 0;
            routes.forEach(r => totalRecords += r.count);
            priceCountEl.textContent = totalRecords + "+";
        }
        
        let lowestPrice = Infinity;
        routes.forEach(r => {
            if (r.min_price < lowestPrice) lowestPrice = r.min_price;
        });
        
        const bestDealEl = document.getElementById('stat-best-deal');
        if (bestDealEl) bestDealEl.textContent = lowestPrice !== Infinity ? formatPrice(lowestPrice) : '₹--';

        // Load Alerts to populate the alerts count card
        const alertResp = await fetch('/api/alerts');
        const alerts = await alertResp.json();
        const activeAlerts = alerts.filter(a => a.is_active).length;
        
        const activeAlertsEl = document.getElementById('stat-active-alerts');
        if (activeAlertsEl) activeAlertsEl.textContent = activeAlerts;

        // Populate Route Selector
        const selector = document.getElementById('route-selector');
        selector.innerHTML = '<option value="">-- Select a Saved Route --</option>';
        
        routes.forEach(r => {
            const opt = document.createElement('option');
            opt.value = `${r.origin}-${r.destination}`;
            opt.textContent = `${getAirportLabel(r.origin)} ✈️ ${getAirportLabel(r.destination)} (from ${formatPrice(r.min_price)})`;
            selector.appendChild(opt);
        });

        selector.onchange = (e) => {
            const val = e.target.value;
            if (val) {
                const [origin, dest] = val.split('-');
                loadRouteDetails(origin, dest);
            } else {
                clearRouteDetails();
            }
        };

    } catch (err) {
        console.error('Error loading dashboard data:', err);
    }
}

// Load detail info for a selected route
async function loadRouteDetails(origin, dest) {
    document.getElementById('selected-route-badge').textContent = `${getAirportLabel(origin)} ➔ ${getAirportLabel(dest)}`;
    document.getElementById('chart-placeholder').style.display = 'none';

    try {
        const response = await fetch(`/api/history?origin=${origin}&destination=${dest}`);
        const flights = await response.json();
        
        // Populate Table
        const tbody = document.querySelector('#flights-table tbody');
        tbody.innerHTML = '';
        
        if (flights.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center">No flights found.</td></tr>';
            return;
        }

        flights.forEach(f => {
            const row = document.createElement('tr');
            
            const durationHrs = Math.floor(f.duration_minutes / 60);
            const durationMins = f.duration_minutes % 60;
            const routeDates = f.return_date ? `${f.departure_date} to ${f.return_date}` : f.departure_date;

            row.innerHTML = `
                <td><strong>${f.airline}</strong></td>
                <td>${routeDates}</td>
                <td><span class="text-emerald" style="font-weight: 600;">${formatPrice(f.price)}</span></td>
                <td>${f.stops === 0 ? 'Non-stop' : `${f.stops} stop(s)`}</td>
                <td>${durationHrs}h ${durationMins}m</td>
                <td>${formatDateTime(f.checked_at)}</td>
            `;
            tbody.appendChild(row);
        });

        // Prepare chart data (prices over time)
        // Group by scan timestamp to plot trend
        const chartPoints = [...flights]
            .reverse() // show oldest first
            .map(f => ({
                x: new Date(f.checked_at),
                y: f.price,
                label: `${f.departure_date} (${f.airline})`
            }));

        renderChart(chartPoints);

    } catch (err) {
        console.error('Error loading route details:', err);
    }
}

function clearRouteDetails() {
    document.getElementById('selected-route-badge').textContent = 'Select a Route';
    document.getElementById('chart-placeholder').style.display = 'flex';
    document.querySelector('#flights-table tbody').innerHTML = '<tr><td colspan="6" class="text-center">Select a route above to load historical scans</td></tr>';
    if (currentChart) {
        currentChart.destroy();
        currentChart = null;
    }
}

// Render line chart with Chart.js
function renderChart(dataPoints) {
    const ctx = document.getElementById('priceTrendChart').getContext('2d');
    
    if (currentChart) {
        currentChart.destroy();
    }

    currentChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dataPoints.map(p => p.x.toLocaleDateString('en-IN', { month: 'short', day: 'numeric', hour: '2-digit' })),
            datasets: [{
                label: 'Round-trip Price',
                data: dataPoints.map(p => p.y),
                borderColor: '#6366f1',
                backgroundColor: 'rgba(99, 102, 241, 0.1)',
                borderWidth: 2.5,
                fill: true,
                tension: 0.35,
                pointBackgroundColor: '#818cf8',
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const point = dataPoints[context.dataIndex];
                            return `Price: ${formatPrice(context.raw)} for ${point.label}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: { color: '#9ca3af' }
                },
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: {
                        color: '#9ca3af',
                        callback: function(value) { return '₹' + value.toLocaleString('en-IN'); }
                    }
                }
            }
        }
    });
}

// Search Form Handler
function initSearchForm() {
    const form = document.getElementById('search-form');
    const consoleCard = document.getElementById('task-monitor-card');
    const logOutput = document.getElementById('console-log-output');
    const statusText = document.getElementById('task-status-text');
    const statusDot = document.getElementById('task-status-dot');
    const submitBtn = document.getElementById('btn-submit-search');

    // Strategy Selection Tabs Toggle logic
    const strategyBtns = document.querySelectorAll('.search-tab-btn');
    const strategyInput = document.getElementById('search-strategy');
    const destWrapper = document.getElementById('destination-field-wrapper');
    const destInput = document.getElementById('search-dest');
    const durationWrapper = document.getElementById('search-duration-wrapper');
    const flexibleDurationWrapper = document.getElementById('flexible-duration-wrapper');
    const budgetFieldWrapper = document.getElementById('budget-field-wrapper');
    const nearbyFieldWrapper = document.getElementById('nearby-field-wrapper');

    strategyBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            strategyBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const strat = btn.getAttribute('data-strategy');
            strategyInput.value = strat;

            if (strat === 'explore') {
                destWrapper.style.display = 'none';
                destInput.removeAttribute('required');
                durationWrapper.style.display = 'block';
                flexibleDurationWrapper.style.display = 'none';
                budgetFieldWrapper.style.display = 'none';
                nearbyFieldWrapper.style.display = 'none';
            } else if (strat === 'flexible') {
                destWrapper.style.display = 'block';
                destInput.setAttribute('required', 'true');
                durationWrapper.style.display = 'none';
                flexibleDurationWrapper.style.display = 'block';
                budgetFieldWrapper.style.display = 'block';
                nearbyFieldWrapper.style.display = 'flex';
            } else {
                destWrapper.style.display = 'block';
                destInput.setAttribute('required', 'true');
                durationWrapper.style.display = 'block';
                flexibleDurationWrapper.style.display = 'none';
                budgetFieldWrapper.style.display = 'none';
                nearbyFieldWrapper.style.display = 'flex';
            }
        });
    });

    document.getElementById('btn-close-console').onclick = () => {
        consoleCard.style.display = 'none';
    };

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const strat = strategyInput.value;
        const sortVal = document.getElementById('search-sort').value;
        
        const originInput = document.getElementById('search-origin');
        originInput.value = resolveAirportInput(originInput.value);
        if (destInput) {
            destInput.value = resolveAirportInput(destInput.value);
        }

        const params = {
            type: strat,
            origin: originInput.value,
            dates: document.getElementById('search-dates').value,
            duration: document.getElementById('search-duration').value,
            min_days: document.getElementById('search-min-days').value,
            max_days: document.getElementById('search-max-days').value,
            budget: document.getElementById('search-budget').value,
            nearby: document.getElementById('search-nearby').checked,
            cabin_class: document.getElementById('search-cabin').value,
            stops_limit: document.getElementById('search-stops').value,
            adults: document.getElementById('search-adults').value
        };

        if (strat !== 'explore') {
            params.destination = destInput.value;
        }

        // Prepare UI loading
        submitBtn.disabled = true;
        submitBtn.textContent = '⏳ Querying Flight Agent...';
        consoleCard.style.display = 'block';
        logOutput.innerHTML = 'Connecting to agent session...\n';
        statusText.textContent = 'Task Status: Starting';
        statusDot.className = 'status-dot pulse yellow';

        try {
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(params)
            });
            const data = await response.json();
            
            if (data.task_id) {
                pollSearchStatus(data.task_id, params.origin, params.destination || null, sortVal);
            } else {
                throw new Error(data.error || 'Failed to start agent');
            }
        } catch (err) {
            logOutput.innerHTML += `\n[ERROR] ${err.message}`;
            submitBtn.disabled = false;
            submitBtn.textContent = '🚀 Start Flight Search';
            statusText.textContent = 'Task Status: Failed';
            statusDot.className = 'status-dot';
        }
    });
}

function pollSearchStatus(taskId, origin, dest, sortVal) {
    const logOutput = document.getElementById('console-log-output');
    const statusText = document.getElementById('task-status-text');
    const statusDot = document.getElementById('task-status-dot');
    const submitBtn = document.getElementById('btn-submit-search');

    if (activeSearchInterval) clearInterval(activeSearchInterval);

    activeSearchInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/search/status/${taskId}`);
            const task = await response.json();

            // Display logs
            logOutput.innerHTML = task.logs.join('\n');
            logOutput.scrollTop = logOutput.scrollHeight;

            if (task.status === 'completed') {
                clearInterval(activeSearchInterval);
                submitBtn.disabled = false;
                submitBtn.textContent = '🚀 Start Flight Search';
                statusText.textContent = 'Task Status: Completed';
                statusDot.className = 'status-dot online';
                loadDashboardData();
                displaySearchResults(task.results, origin, dest, sortVal);
            } else if (task.status === 'failed') {
                clearInterval(activeSearchInterval);
                submitBtn.disabled = false;
                submitBtn.textContent = '🚀 Start Flight Search';
                statusText.textContent = 'Task Status: Failed';
                statusDot.className = 'status-dot';
            }
        } catch (err) {
            console.error('Polling error:', err);
        }
    }, 1000);
}

// Alerts Management
function initAlerts() {
    const form = document.getElementById('alert-form');
    
    // Set default dates to today / + 1 month
    const today = new Date();
    const nextMonth = new Date();
    nextMonth.setMonth(today.getMonth() + 1);

    document.getElementById('alert-start').value = today.toISOString().split('T')[0];
    document.getElementById('alert-end').value = nextMonth.toISOString().split('T')[0];

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const originInput = document.getElementById('alert-origin');
        const destInput = document.getElementById('alert-dest');
        originInput.value = resolveAirportInput(originInput.value);
        destInput.value = resolveAirportInput(destInput.value);

        const params = {
            origin: originInput.value,
            destination: destInput.value,
            departure_date_start: document.getElementById('alert-start').value,
            departure_date_end: document.getElementById('alert-end').value,
            trip_duration_days: document.getElementById('alert-duration').value,
            target_price: document.getElementById('alert-target').value
        };

        try {
            const response = await fetch('/api/alerts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(params)
            });
            const data = await response.json();
            
            if (response.ok) {
                form.reset();
                loadAlerts();
            } else {
                alert(data.error || 'Failed to create alert');
            }
        } catch (err) {
            console.error(err);
        }
    });
}

async function loadAlerts() {
    const container = document.getElementById('alerts-list-container');
    
    try {
        const response = await fetch('/api/alerts');
        const alerts = await response.json();

        if (alerts.length === 0) {
            container.innerHTML = '<p class="text-center text-muted">No alerts set yet.</p>';
            return;
        }

        container.innerHTML = '';
        alerts.forEach(a => {
            const item = document.createElement('div');
            item.className = 'alert-item';
            
            const bestPriceText = a.best_price_found 
                ? `<span class="best-found">Best found: ${formatPrice(a.best_price_found)} (${a.best_date_found})</span>`
                : '<span class="text-muted" style="font-size:12px;">No price records yet</span>';

            item.innerHTML = `
                <div class="alert-info">
                    <h4>${a.origin} ✈️ ${a.destination}</h4>
                    <p>Range: ${a.departure_date_start} to ${a.departure_date_end} | ${a.trip_duration_days} days</p>
                    <p style="margin-top:4px;">${bestPriceText}</p>
                </div>
                <div class="alert-price-block">
                    <span class="target-price">Target: ${formatPrice(a.target_price)}</span>
                    <span class="badge ${a.is_active ? 'badge-active' : 'badge-triggered'}" style="background:${a.is_active ? 'rgba(16,185,129,0.15)' : 'rgba(244,63,94,0.15)'}; color:${a.is_active ? '#10b981' : '#f43f5e'}; border-color:${a.is_active ? 'rgba(16,185,129,0.25)' : 'rgba(244,63,94,0.25)'}">
                        ${a.is_active ? 'Active' : 'Triggered'}
                    </span>
                    <button class="btn btn-danger btn-sm" onclick="deleteAlert(${a.id})" style="padding: 4px 8px; font-size: 11px;">
                        Delete
                    </button>
                </div>
            `;
            container.appendChild(item);
        });
    } catch (err) {
        console.error(err);
    }
}

async function deleteAlert(id) {
    if (!confirm('Are you sure you want to delete this alert?')) return;
    try {
        const response = await fetch(`/api/alerts/${id}`, { method: 'DELETE' });
        if (response.ok) {
            loadAlerts();
        }
    } catch (err) {
        console.error(err);
    }
}

async function scanAlerts() {
    const scanBtn = document.getElementById('btn-trigger-alerts');
    scanBtn.disabled = true;
    scanBtn.textContent = '⏳ Scanning...';
    
    try {
        const response = await fetch('/api/alerts/check', { method: 'POST' });
        if (response.ok) {
            alert('Background price scanner triggered! The agent is checking routes in the background.');
            setTimeout(() => {
                loadAlerts();
                scanBtn.disabled = false;
                scanBtn.textContent = '🔄 Scan Alerts';
            }, 3000);
        }
    } catch (err) {
        console.error(err);
        scanBtn.disabled = false;
        scanBtn.textContent = '🔄 Scan Alerts';
    }
}

function displaySearchResults(results, origin, dest, sortVal = 'score') {
    const card = document.getElementById('search-results-card');
    const badge = document.getElementById('results-count-badge');
    const nearbyContainer = document.getElementById('nearby-savings-container');
    const nearbyList = document.getElementById('nearby-savings-list');
    const resultsList = document.getElementById('search-results-list');
    
    let flightsList = [];
    let alternativesList = [];
    
    if (results && !Array.isArray(results) && results.primary) {
        flightsList = results.primary;
        alternativesList = results.alternatives || [];
    } else {
        flightsList = results || [];
    }
    
    if (!flightsList || flightsList.length === 0) {
        resultsList.innerHTML = '<p class="text-center text-muted" style="padding: 30px;">No quality flights found matching search criteria.</p>';
        badge.textContent = '0 flights';
        nearbyContainer.style.display = 'none';
        card.style.display = 'block';
        return;
    }
    
    resultsList.innerHTML = '';
    badge.textContent = `${flightsList.length} flight(s)`;
    
    // Sort dynamically based on user criteria
    let sorted = [...flightsList];
    if (sortVal === 'price') {
        sorted.sort((a, b) => {
            const priceA = a.price === null || a.price === undefined ? Infinity : a.price;
            const priceB = b.price === null || b.price === undefined ? Infinity : b.price;
            return priceA - priceB;
        });
    } else if (sortVal === 'duration') {
        sorted.sort((a, b) => {
            const durA = a.duration || a.duration_minutes || 999999;
            const durB = b.duration || b.duration_minutes || 999999;
            return durA - durB;
        });
    } else {
        // Value Score sort (descending)
        sorted.sort((a, b) => {
            const scoreA = a.score_data ? a.score_data.score : 0;
            const scoreB = b.score_data ? b.score_data.score : 0;
            return scoreB - scoreA;
        });
    }

    // Split into featured (top 5) and remaining
    const featured = sorted.slice(0, 5);
    const remaining = sorted.slice(5);

    // ═══════════════════════════════════════════════
    // Section: Top Picks (Featured Cards)
    // ═══════════════════════════════════════════════
    const featuredHeader = document.createElement('div');
    featuredHeader.className = 'results-section-header';
    featuredHeader.innerHTML = `🏆 Top ${Math.min(5, sorted.length)} Picks <span class="count-badge">${featured.length}</span>`;
    resultsList.appendChild(featuredHeader);

    featured.forEach((f, idx) => {
        const article = _buildFeaturedCard(f, idx, origin, dest);
        resultsList.appendChild(article);
    });

    // ═══════════════════════════════════════════════
    // Section: More Options (Compact Rows)
    // ═══════════════════════════════════════════════
    if (remaining.length > 0) {
        const moreHeader = document.createElement('div');
        moreHeader.className = 'results-section-header';
        moreHeader.style.marginTop = 'var(--space-6)';
        moreHeader.innerHTML = `📋 More Options <span class="count-badge">${remaining.length}</span>`;
        resultsList.appendChild(moreHeader);

        const compactList = document.createElement('div');
        compactList.className = 'results-compact-list';
        
        remaining.forEach((f, idx) => {
            const row = _buildCompactRow(f, idx + 5, origin, dest);
            compactList.appendChild(row);
        });
        
        resultsList.appendChild(compactList);
    }

    // Nearby airport savings rendering
    if (alternativesList && alternativesList.length > 0) {
        nearbyList.innerHTML = '';
        alternativesList.forEach(alt => {
            const savingsText = alt.savings > 0 
                ? `<span style="font-weight: 700; color: var(--success);">Save ${formatPrice(alt.savings)}!</span>` 
                : `<span class="text-muted">No additional savings</span>`;
            
            const div = document.createElement('div');
            div.style.display = 'flex';
            div.style.justifyContent = 'space-between';
            div.style.alignItems = 'center';
            div.style.fontSize = '13px';
            div.style.padding = '10px 14px';
            div.style.background = 'rgba(255, 255, 255, 0.02)';
            div.style.borderRadius = '8px';
            div.style.border = '1px solid var(--border-subtle)';
            
            div.innerHTML = `
                <div>
                    <strong>Fly from ${getAirportLabel(alt.origin)}</strong> instead of ${getAirportLabel(origin)}: 
                    <span style="color: var(--cyan-500); font-weight: 600;">${formatPrice(alt.price)}</span> via ${alt.airline} on ${alt.departure_date}
                </div>
                <div>
                    ${savingsText}
                </div>
            `;
            nearbyList.appendChild(div);
        });
        nearbyContainer.style.display = 'block';
    } else {
        nearbyContainer.style.display = 'none';
    }
    
    card.style.display = 'block';
    card.scrollIntoView({ behavior: 'smooth' });
}

// ═══════════════════════════════════════════════════
// BUILDER: Featured Card (rich card for top 5)
// ═══════════════════════════════════════════════════
function _buildFeaturedCard(f, idx, origin, dest) {
    const article = document.createElement('article');
    article.className = 'flight-card';
    
    // Dates formatting
    const routeDates = f.return_date ? `${f.departure_date} ➔ ${f.return_date}` : f.departure_date;
    
    // Duration formatting
    const hrs = Math.floor((f.duration || f.duration_minutes || 0) / 60);
    const mins = (f.duration || f.duration_minutes || 0) % 60;
    const durationText = (f.duration || f.duration_minutes) ? `${hrs}h ${mins}m` : '--';
    
    // Target destination if explore (where destination is variable)
    const currentDest = dest || f.destination;
    
    // Link creation
    const bookingQuery = f.return_date 
        ? `Flights from ${origin} to ${currentDest} on ${f.departure_date} return ${f.return_date}`
        : `Flights from ${origin} to ${currentDest} on ${f.departure_date}`;
    const bookingUrl = `https://www.google.com/travel/flights?q=${encodeURIComponent(bookingQuery)}`;
    
    // Score value & color
    const score = f.score_data ? f.score_data.score : 70;
    const label = f.score_data ? f.score_data.label : 'Fair Deal';
    let strokeColor = '#00d4ff';
    if (score >= 85) strokeColor = '#10b981';
    else if (score >= 70) strokeColor = '#00d4ff';
    else if (score >= 55) strokeColor = '#f59e0b';
    else strokeColor = '#ef4444';
    
    // Price comparison formatting
    let priceComparisonHtml = '';
    if (f.price === null || f.price === undefined) {
        priceComparisonHtml = `<span class="price-comparison price-comparison--neutral">no current price</span>`;
    } else if (f.prediction && f.prediction.historical_avg) {
        const avg = f.prediction.historical_avg;
        const diffPercent = Math.round(((avg - f.price) / avg) * 100);
        if (diffPercent > 0) {
            priceComparisonHtml = `<span class="price-comparison price-comparison--good">↓ ${diffPercent}% below avg</span>`;
        } else if (diffPercent < 0) {
            priceComparisonHtml = `<span class="price-comparison price-comparison--bad">↑ ${Math.abs(diffPercent)}% above avg</span>`;
        } else {
            priceComparisonHtml = `<span class="price-comparison price-comparison--neutral">avg price</span>`;
        }
    } else {
        priceComparisonHtml = `<span class="price-comparison price-comparison--neutral">calculating average</span>`;
    }

    // Airline initials
    const airlineName = f.airlines ? f.airlines.join(' / ') : (f.airline || 'Unknown');
    const initials = airlineName.substring(0, 2).toUpperCase();

    // Insight recommendations
    let actionColor = 'var(--text-secondary)';
    let actionSymbol = '⚪';
    let insightActionText = 'FAIR PRICE';
    let confidenceText = '50%';
    let reasonText = 'No price history prediction data available yet.';
    
    if (f.prediction) {
        insightActionText = f.prediction.action;
        confidenceText = f.prediction.confidence + '%';
        reasonText = f.prediction.reason;
        if (f.prediction.action === 'BUY NOW') {
            actionColor = 'var(--success)';
            actionSymbol = '🟢';
        } else if (f.prediction.action === 'WAIT') {
            actionColor = 'var(--danger)';
            actionSymbol = '🔴';
        } else if (f.prediction.action === 'FAIR PRICE') {
            actionColor = 'var(--warning)';
            actionSymbol = '🟡';
        }
    }

    // Layover chip
    let layoverHtml = '';
    if (f.stops > 0) {
        layoverHtml = `
            <div class="flight-card__layover">
                <div class="layover-chip">
                    <span class="layover-chip__label">${f.stops} stop(s)</span>
                    <span class="layover-chip__detail">${airlineName}</span>
                    <span class="layover-chip__duration">${durationText}</span>
                </div>
            </div>
        `;
    } else {
        layoverHtml = `
            <div class="flight-card__layover">
                <div class="layover-chip">
                    <span class="layover-chip__bonus" style="color: var(--success); font-weight: 600;">⚡ Non-stop flight</span>
                </div>
            </div>
        `;
    }

    article.innerHTML = `
        <!-- Card Header -->
        <div class="flight-card__header">
            <div class="flight-card__rank">
                <span class="rank-badge rank-badge--gold">🏆 #${idx + 1}</span>
                <span class="rank-label">${label.toUpperCase()}</span>
            </div>
            <div class="flight-card__score">
                <div class="score-ring">
                    <svg viewBox="0 0 36 36" class="score-ring__svg">
                        <path class="score-ring__bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"/>
                        <path class="score-ring__fill" stroke="${strokeColor}" stroke-dasharray="${score}, 100" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"/>
                    </svg>
                    <span class="score-ring__value">${score}</span>
                </div>
            </div>
        </div>
        
        <!-- Card Body -->
        <div class="flight-card__body">
            <div class="flight-card__route">
                <div class="airline-badge">
                    <div style="width: 36px; height: 36px; border-radius: var(--radius-sm); background: linear-gradient(135deg, var(--cyan-600), var(--violet-600)); display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 13px; color: white; border: 1px solid var(--border-strong);">
                        ${initials}
                    </div>
                    <span class="airline-code">${initials}</span>
                </div>
                
                <div class="route-visual">
                    <div class="route-point route-point--origin">
                        <span class="route-code">${origin}</span>
                        <span class="route-date">${f.departure_date}</span>
                    </div>
                    
                    <div class="route-line">
                        <div class="route-line__track"></div>
                        ${f.stops > 0 ? `
                        <div class="route-line__stop">
                            <span class="stop-dot"></span>
                        </div>` : ''}
                        <span class="route-line__duration">${durationText}</span>
                    </div>
                    
                    <div class="route-point route-point--dest">
                        <span class="route-code">${currentDest}</span>
                        <span class="route-date">${f.return_date || f.departure_date}</span>
                    </div>
                </div>
                
                <div class="flight-card__price">
                    <span class="price-amount">${f.price === null || f.price === undefined ? 'Check Fare' : formatPrice(f.price)}</span>
                    ${priceComparisonHtml}
                </div>
            </div>
            
            ${layoverHtml}
            
            <div class="flight-card__quality">
                <div class="quality-bar">
                    <div class="quality-bar__fill" style="width: ${score}%"></div>
                </div>
                <div class="quality-details">
                    <span class="quality-tag">Airline quality score: ${score}/100</span>
                    <span class="quality-tag">Airline: ${airlineName}</span>
                </div>
            </div>
        </div>
        
        <!-- AI Insight Section -->
        <div class="flight-card__insight">
            <span class="insight-icon">${actionSymbol}</span>
            <p class="insight-text">
                Recommendation: <strong style="color: ${actionColor}; font-weight: 700;">${insightActionText}</strong> (${confidenceText} confidence) — ${reasonText}
            </p>
        </div>
        
        <!-- Card Actions -->
        <div class="flight-card__actions">
            <button class="card-action" onclick="createAlertFromFlight('${origin}', '${currentDest}', '${f.departure_date}', '${f.return_date || ''}', ${f.price !== null && f.price !== undefined ? f.price : 'null'})">
                <span>🔔 Track Route</span>
            </button>
            <button class="card-action" onclick="window.location.hash='#/analytics'; setTimeout(() => { loadRouteDetails('${origin}', '${currentDest}') }, 100)">
                <span>📊 Price History</span>
            </button>
            <a href="${bookingUrl}" target="_blank" class="card-action card-action--gradient">
                <span>🎟️ Book Now ↗</span>
            </a>
        </div>
    `;
    return article;
}

// ═══════════════════════════════════════════════════
// BUILDER: Compact Row (for remaining results)
// ═══════════════════════════════════════════════════
function _buildCompactRow(f, idx, origin, dest) {
    const row = document.createElement('div');
    row.className = 'result-row';
    
    const currentDest = dest || f.destination;
    const airlineName = f.airlines ? f.airlines.join(' / ') : (f.airline || 'Unknown');
    const hrs = Math.floor((f.duration || f.duration_minutes || 0) / 60);
    const mins = (f.duration || f.duration_minutes || 0) % 60;
    const durationText = (f.duration || f.duration_minutes) ? `${hrs}h ${mins}m` : '--';
    const stopsText = f.stops === 0 ? 'Direct' : `${f.stops} stop${f.stops > 1 ? 's' : ''}`;
    const score = f.score_data ? f.score_data.score : 70;
    
    const bookingQuery = f.return_date 
        ? `Flights from ${origin} to ${currentDest} on ${f.departure_date} return ${f.return_date}`
        : `Flights from ${origin} to ${currentDest} on ${f.departure_date}`;
    const bookingUrl = `https://www.google.com/travel/flights?q=${encodeURIComponent(bookingQuery)}`;
    
    const priceDisplay = f.price === null || f.price === undefined ? 'Check Fare' : formatPrice(f.price);
    
    row.innerHTML = `
        <div class="result-row__route">
            <span class="result-row__route-name">${getAirportCity(origin)} → ${getAirportCity(currentDest)}</span>
            <span class="result-row__route-codes">${origin} → ${currentDest}</span>
            <div class="result-row__meta">${f.departure_date}${f.return_date ? ' ↔ ' + f.return_date : ''} · ${durationText} · ${stopsText} · ${airlineName}</div>
        </div>
        <span class="result-row__score">⚡ ${score}</span>
        <span class="result-row__price">${priceDisplay}</span>
        <div class="result-row__actions">
            <a href="${bookingUrl}" target="_blank" class="action-icon-btn action-icon-btn--book" title="Book this flight">🔗</a>
            <button class="action-icon-btn" title="Track this route" onclick="createAlertFromFlight('${origin}', '${currentDest}', '${f.departure_date}', '${f.return_date || ''}', ${f.price !== null && f.price !== undefined ? f.price : 'null'})">🔔</button>
        </div>
    `;
    return row;
}

window.createAlertFromFlight = async (origin, dest, start, end, price) => {
    // Switch to alerts view
    const navBtns = document.querySelectorAll('.nav-link-btn');
    const viewWorkspace = document.getElementById('view-workspace');
    const viewLanding = document.getElementById('view-landing');
    const workTabs = document.querySelectorAll('.workspace-tab-content');
    
    // Switch navigation states
    navBtns.forEach(btn => {
        if (btn.getAttribute('data-view') === 'alerts') {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
    
    viewLanding.classList.remove('active');
    viewWorkspace.style.display = 'block';
    workTabs.forEach(tab => {
        if (tab.id === 'work-alerts') {
            tab.classList.add('active');
            tab.style.display = 'block';
        } else {
            tab.classList.remove('active');
            tab.style.display = 'none';
        }
    });
    
    // Populate form fields
    document.getElementById('alert-origin').value = origin;
    document.getElementById('alert-dest').value = dest;
    document.getElementById('alert-start').value = start;
    if (end) {
        document.getElementById('alert-end').value = end;
        // calculate duration
        const d1 = new Date(start);
        const d2 = new Date(end);
        const duration = Math.max(1, Math.round((d2 - d1) / (1000 * 60 * 60 * 24)));
        document.getElementById('alert-duration').value = duration;
    } else {
        document.getElementById('alert-end').value = start;
        document.getElementById('alert-duration').value = 7;
    }
    document.getElementById('alert-target').value = price !== null && price !== undefined ? Math.round(price * 0.9) : '';
    
    // Scroll to form
    document.getElementById('alert-form').scrollIntoView({ behavior: 'smooth' });
};
