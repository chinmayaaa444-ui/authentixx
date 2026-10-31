
/* =====================================
   AUTHENTIX — INTERACTIVE EXPERIENCE
===================================== */


/* 1. CURSOR SPOTLIGHT */

const root = document.documentElement;

document.addEventListener("mousemove", (event) => {
    root.style.setProperty("--mouse-x", event.clientX + "px");
    root.style.setProperty("--mouse-y", event.clientY + "px");
});


/* 2. INTERACTIVE PARTICLE BACKGROUND */

const particleCanvas = document.getElementById("particles");
const particleCtx = particleCanvas
    ? particleCanvas.getContext("2d")
    : null;

let particles = [];

let mouse = {
    x: null,
    y: null,
    radius: 150
};

function resizeCanvas() {

    if (!particleCanvas || !particleCtx) return;

    const ratio = Math.min(window.devicePixelRatio || 1, 2);

    particleCanvas.width = window.innerWidth * ratio;
    particleCanvas.height = window.innerHeight * ratio;

    particleCanvas.style.width = window.innerWidth + "px";
    particleCanvas.style.height = window.innerHeight + "px";

    particleCtx.setTransform(ratio, 0, 0, ratio, 0, 0);

    createParticles();
}

function createParticles() {

    particles = [];

    const count = Math.min(
        110,
        Math.floor(window.innerWidth / 12)
    );

    for (let i = 0; i < count; i++) {

        particles.push({
            x: Math.random() * window.innerWidth,
            y: Math.random() * window.innerHeight,
            size: Math.random() * 2 + 0.5,
            speedX: (Math.random() - 0.5) * 0.6,
            speedY: (Math.random() - 0.5) * 0.6,
            opacity: Math.random() * 0.6 + 0.2
        });

    }
}

function drawParticles() {

    if (!particleCtx) return;

    particleCtx.clearRect(
        0,
        0,
        window.innerWidth,
        window.innerHeight
    );

    particles.forEach((particle, index) => {

        particle.x += particle.speedX;
        particle.y += particle.speedY;

        if (particle.x < 0 ||
            particle.x > window.innerWidth) {
            particle.speedX *= -1;
        }

        if (particle.y < 0 ||
            particle.y > window.innerHeight) {
            particle.speedY *= -1;
        }

        if (mouse.x !== null && mouse.y !== null) {

            const dx = mouse.x - particle.x;
            const dy = mouse.y - particle.y;

            const distance = Math.sqrt(dx * dx + dy * dy);

            if (distance < mouse.radius && distance > 0) {

                particle.x -= dx / distance * 0.7;
                particle.y -= dy / distance * 0.7;

            }
        }

        particleCtx.beginPath();

        particleCtx.arc(
            particle.x,
            particle.y,
            particle.size,
            0,
            Math.PI * 2
        );

        particleCtx.fillStyle =
            `rgba(75, 235, 155, ${particle.opacity})`;

        particleCtx.fill();

        for (let j = index + 1; j < particles.length; j++) {

            const other = particles[j];

            const dx = particle.x - other.x;
            const dy = particle.y - other.y;

            const distance = Math.sqrt(dx * dx + dy * dy);

            if (distance < 115) {

                const opacity = 0.16 * (1 - distance / 115);

                particleCtx.beginPath();
                particleCtx.moveTo(particle.x, particle.y);
                particleCtx.lineTo(other.x, other.y);

                particleCtx.strokeStyle =
                    `rgba(53, 217, 154, ${opacity})`;

                particleCtx.lineWidth = 0.7;
                particleCtx.stroke();

            }
        }
    });

    requestAnimationFrame(drawParticles);
}

document.addEventListener("mousemove", (event) => {
    mouse.x = event.clientX;
    mouse.y = event.clientY;
});

document.addEventListener("mouseleave", () => {
    mouse.x = null;
    mouse.y = null;
});

window.addEventListener("resize", resizeCanvas);

if (particleCanvas && particleCtx) {
    resizeCanvas();
    drawParticles();
}


/* 3. MAGNETIC BUTTONS */

const magneticElements =
    document.querySelectorAll(".magnetic");

magneticElements.forEach((element) => {

    element.addEventListener("mousemove", (event) => {

        const rect = element.getBoundingClientRect();

        const x = event.clientX - rect.left - rect.width / 2;
        const y = event.clientY - rect.top - rect.height / 2;

        element.style.transform =
            `translate(${x * 0.12}px, ${y * 0.12}px)`;

    });

    element.addEventListener("mouseleave", () => {
        element.style.transform = "translate(0, 0)";
    });

});


/* 4. 3D CARD TILT EFFECT */

const tiltCards = document.querySelectorAll(".tilt-card");

tiltCards.forEach((card) => {

    card.addEventListener("mousemove", (event) => {

        const rect = card.getBoundingClientRect();

        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;

        const centerX = rect.width / 2;
        const centerY = rect.height / 2;

        const rotateX = ((centerY - y) / centerY) * 7;
        const rotateY = ((x - centerX) / centerX) * 7;

        card.style.transform =
            `perspective(1000px)
             rotateX(${rotateX}deg)
             rotateY(${rotateY}deg)
             translateY(-4px)`;

        card.style.setProperty("--card-x", x + "px");
        card.style.setProperty("--card-y", y + "px");

    });

    card.addEventListener("mouseleave", () => {
        card.style.transform = "";
    });

});


/* 5. SCROLL REVEAL ANIMATION */

const revealElements = document.querySelectorAll(".reveal");

if ("IntersectionObserver" in window) {

    const revealObserver = new IntersectionObserver(
        (entries) => {

            entries.forEach((entry) => {

                if (entry.isIntersecting) {

                    entry.target.classList.add("visible");
                    revealObserver.unobserve(entry.target);

                }

            });

        },
        {
            threshold: 0.12
        }
    );

    revealElements.forEach((element) => {
        revealObserver.observe(element);
    });

} else {

    revealElements.forEach((element) => {
        element.classList.add("visible");
    });

}


/* 6. ANIMATED DASHBOARD COUNTERS */

const counters = document.querySelectorAll(".counter");

if ("IntersectionObserver" in window) {

    const counterObserver = new IntersectionObserver(
        (entries) => {

            entries.forEach((entry) => {

                if (entry.isIntersecting) {

                    const counter = entry.target;
                    const target = Number(counter.dataset.target);

                    const duration = 1600;
                    const startTime = performance.now();

                    function updateCounter(currentTime) {

                        const progress = Math.min(
                            (currentTime - startTime) / duration,
                            1
                        );

                        const eased = 1 - Math.pow(1 - progress, 3);

                        counter.textContent =
                            Math.floor(target * eased);

                        if (progress < 1) {
                            requestAnimationFrame(updateCounter);
                        }

                    }

                    requestAnimationFrame(updateCounter);

                    counterObserver.unobserve(counter);

                }

            });

        },
        {
            threshold: 0.5
        }
    );

    counters.forEach((counter) => {
        counterObserver.observe(counter);
    });

}


/* =====================================
   7. AUTHENTIX MESSAGE SCANNER
===================================== */

const scanButton = document.getElementById("scanButton");
const messageInput = document.getElementById("messageInput");
const scanResult = document.getElementById("scanResult");
const riskMeter = document.getElementById("riskMeter");
const riskScore = document.getElementById("riskScore");
const riskFill = document.getElementById("riskFill");
const riskLevel = document.getElementById("riskLevel");

function updateRiskMeter(score) {
    const numericScore = Number(score);

    if (
        !Number.isFinite(numericScore) ||
        !riskMeter ||
        !riskScore ||
        !riskFill ||
        !riskLevel
    ) return;

    const value = Math.round(
        Math.max(0, Math.min(100, numericScore))
    );

    let level;
    let category;

    if (value === 0) {
        level = "No obvious warning signs";
        category = "no-risk";
    } else if (value < 25) {
        level = "Low Risk";
        category = "low";
    } else if (value < 50) {
        level = "Moderate Risk";
        category = "moderate";
    } else if (value < 75) {
        level = "High Risk";
        category = "high";
    } else {
        level = "Very High Risk";
        category = "very-high";
    }

    riskMeter.hidden = false;

    riskMeter.className = "risk-meter";
    riskMeter.classList.add(category);

    riskScore.textContent = `${value}/100`;
    riskLevel.textContent = level;

    riskFill.style.width = "0%";

    requestAnimationFrame(() => {
        riskFill.style.width = `${value}%`;
    });
}
if (scanButton && messageInput && scanResult) {

    scanButton.addEventListener("click", async () => {

        const message = messageInput.value.trim();

        if (!message) {

            scanResult.textContent =
                "Please enter a message first.";

            messageInput.focus();
            return;

        }

        scanButton.disabled = true;
if (riskMeter) {
    riskMeter.hidden = true;
    if (riskFill) riskFill.style.width = "0%";
}
        scanButton.textContent = "Analysing Message...";

        scanResult.textContent =
            "Authentix is analysing your message...";

        try {

            const response = await fetch("/api/analyze", {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    message: message
                })

            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Message analysis failed.");
            }

            scanResult.textContent = data.result;
           await refreshDashboard();
if (data.risk_score !== undefined) {
    updateRiskMeter(data.risk_score);
} else {
    console.error("Risk score missing from Flask response:", data);
}

        } catch (error) {

            console.error("Message scanner error:", error);

            scanResult.textContent =
                "Unable to connect to Authentix. Please try again.";

        } finally {

            scanButton.disabled = false;
            scanButton.textContent = "Analyse Message ↗";

        }

    });

}


/* =====================================
   8. AUTHENTIX WEBSITE URL SCANNER
===================================== */

const urlInput = document.getElementById("urlInput");
const urlScanButton = document.getElementById("urlScanButton");
const urlScanResult = document.getElementById("urlScanResult");

if (urlInput && urlScanButton && urlScanResult) {

    urlScanButton.addEventListener("click", async () => {

        const url = urlInput.value.trim();

        if (!url) {

            urlScanResult.textContent =
                "Please enter a website URL.";

            urlInput.focus();
            return;

        }

        urlScanButton.disabled = true;
        urlScanButton.textContent = "Checking Website...";

        urlScanResult.textContent =
            "Authentix is checking the website address...";

        try {

            const response = await fetch("/api/analyze-url", {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    url: url
                })

            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Website analysis failed.");
            }

            urlScanResult.textContent = data.result;
           await refreshDashboard();

        } catch (error) {

            console.error("Website scanner error:", error);

            urlScanResult.textContent =
                "Unable to connect to Authentix. Please try again.";

        } finally {

            urlScanButton.disabled = false;
            urlScanButton.textContent = "Analyse Website ↗";

        }

    });

}


/* 9. MOBILE POINTER SUPPORT */

if (window.matchMedia("(pointer: coarse)").matches) {

    const cursorGlow = document.querySelector(".cursor-glow");

    if (cursorGlow) {
        cursorGlow.style.display = "none";
    }

}


/* 10. PREMIUM CURSOR TRAIL */

const trail = document.createElement("div");

trail.className = "cursor-trail";
document.body.appendChild(trail);

let trailX = 0;
let trailY = 0;

document.addEventListener("mousemove", (event) => {
    trailX = event.clientX;
    trailY = event.clientY;
});

function animateTrail() {

    const currentX = parseFloat(trail.style.left) || trailX;
    const currentY = parseFloat(trail.style.top) || trailY;

    trail.style.left =
        currentX + (trailX - currentX) * 0.18 + "px";

    trail.style.top =
        currentY + (trailY - currentY) * 0.18 + "px";

    requestAnimationFrame(animateTrail);
}

animateTrail();


/* =========================================
   11. AUTHENTIX — ANIMATED PARTICLE HAND LOGO
========================================= */

(function () {

    const handCanvas = document.getElementById("authentixHand");

    if (!handCanvas) return;

    const ctx = handCanvas.getContext("2d");
    const logo = document.getElementById("authentixLogo");

    if (!ctx || !logo) return;

    const SIZE = 60;
    const DPR = Math.min(window.devicePixelRatio || 1, 2);

    handCanvas.width = SIZE * DPR;
    handCanvas.height = SIZE * DPR;

    ctx.scale(DPR, DPR);

    const S = SIZE / 100;

    const off = document.createElement("canvas");

    off.width = 100;
    off.height = 100;

    const o = off.getContext("2d");

    o.fillStyle = "#fff";
    o.strokeStyle = "#fff";
    o.lineCap = "round";

    // Palm

    o.beginPath();
    o.roundRect(30, 52, 42, 34, 13);
    o.fill();

    // Fingers and thumb

    o.lineWidth = 9;

    [
        [36, 54, 36, 26],
        [46, 52, 46, 17],
        [56, 54, 56, 23],
        [66, 58, 68, 34],
        [33, 68, 15, 48]
    ].forEach(([a, b, c, d]) => {

        o.beginPath();
        o.moveTo(a, b);
        o.lineTo(c, d);
        o.stroke();

    });

    // Convert hand shape into particles

    const data = o.getImageData(0, 0, 100, 100).data;

    const particles = [];

    for (let y = 4; y < 100; y += 4) {

        for (let x = 4; x < 100; x += 4) {

            if (data[(y * 100 + x) * 4 + 3] > 128) {

                particles.push({

                    tx: x + (Math.random() - 0.5) * 2,
                    ty: y + (Math.random() - 0.5) * 2,

                    x: Math.random() * 100,
                    y: Math.random() * 100,

                    vx: 0,
                    vy: 0,

                    ph: Math.random() * 6.28,

                    r: 0.8 + Math.random() * 0.9

                });

            }

        }

    }

    let hover = false;
    let t = 0;
    let scatterT = 0;

    function scatter() {

        particles.forEach((p) => {

            const angle = Math.random() * 6.28;
            const force = 2 + Math.random() * 4;

            p.vx = Math.cos(angle) * force;
            p.vy = Math.sin(angle) * force;

        });

    }

    logo.addEventListener("mouseenter", () => {

        hover = true;
        scatter();

    });

    logo.addEventListener("mouseleave", () => {

        hover = false;

    });

    function animate() {

        t += 0.016;
        scatterT += 0.016;

        if (scatterT > 7) {

            scatterT = 0;
            scatter();

        }

        ctx.clearRect(0, 0, SIZE, SIZE);

        const wave = (t * 0.6) % 1.6 * 100;

        // Particle movement

        particles.forEach((p) => {

            const k = hover ? 0.015 : 0.06;

            p.vx +=
                (p.tx - p.x) * k +
                Math.sin(t * 2 + p.ph) * 0.03;

            p.vy +=
                (p.ty - p.y) * k +
                Math.cos(t * 2 + p.ph) * 0.03;

            p.vx *= 0.86;
            p.vy *= 0.86;

            p.x += p.vx;
            p.y += p.vy;

        });

        // Connect nearby particles

        ctx.lineWidth = 0.5;

        for (let i = 0; i < particles.length; i++) {

            for (let j = i + 1; j < particles.length; j++) {

                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;

                const distanceSquared = dx * dx + dy * dy;

                if (distanceSquared < 90) {

                    ctx.strokeStyle =
                        `rgba(52,211,153,${0.35 * (1 - distanceSquared / 90)})`;

                    ctx.beginPath();

                    ctx.moveTo(
                        particles[i].x * S,
                        particles[i].y * S
                    );

                    ctx.lineTo(
                        particles[j].x * S,
                        particles[j].y * S
                    );

                    ctx.stroke();

                }

            }

        }

        // Draw glowing particles and scanning light

        particles.forEach((p) => {

            const near = Math.max(
                0,
                1 - Math.abs((100 - p.y) - wave + 30) / 14
            );

            ctx.fillStyle = near > 0.05
                ? `rgba(167,243,208,${0.6 + near * 0.4})`
                : "rgba(52,211,153,0.85)";

            ctx.beginPath();

            ctx.arc(
                p.x * S,
                p.y * S,
                (p.r + near * 0.9) * S * 0.8,
                0,
                6.28
            );

            ctx.fill();

        });

        requestAnimationFrame(animate);

    }

    animate();

})();

/* =====================================
   6. REAL-TIME AUTHENTIX DASHBOARD
===================================== */

async function refreshDashboard() {
    try {
        const response = await fetch("/api/dashboard");

        if (!response.ok) {
            throw new Error("Dashboard data could not be loaded.");
        }

        const stats = await response.json();

        const total = document.getElementById("totalScans");
        const lowRisk = document.getElementById("safeScans");
        const flagged = document.getElementById("flaggedScans");
        const activity = document.getElementById("recentActivity");

        if (total) total.textContent = stats.total_scans;
        if (lowRisk) lowRisk.textContent = stats.low_risk_scans;
        if (flagged) flagged.textContent = stats.flagged_scans;

        if (activity) {
            activity.replaceChildren();

            if (!stats.recent_activity.length) {
                const empty = document.createElement("p");
                empty.textContent =
                    "No scans yet. Try scanning a message or website!";
                activity.appendChild(empty);
            } else {
                stats.recent_activity.forEach((scan) => {
                    const item = document.createElement("div");
                    item.className = "activity-item";

                    const heading = document.createElement("strong");
                    heading.textContent = scan.scan_type + " Scan";

                    const details = document.createElement("p");
                    details.textContent =
                        scan.risk_level + " · " + scan.risk_score + "/100";

                    const date = document.createElement("small");
                    date.textContent =
                        new Date(scan.created_at).toLocaleString();

                    item.append(heading, details, date);
                    activity.appendChild(item);
                });
            }
        }
    } catch (error) {
        console.error("Dashboard error:", error);
    }
}

document.addEventListener("DOMContentLoaded", refreshDashboard);

