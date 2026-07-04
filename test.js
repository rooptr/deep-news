



        const options = { weekday: 'long', month: 'long', day: 'numeric' };
        document.getElementById('date-text').innerText = new Date().toLocaleDateString('en-US', options);

        // Force browser to fetch the absolute latest PDFs and Images by appending a timestamp
        const cacheBuster = '?v=' + new Date().getTime();
        document.querySelectorAll('.topping').forEach(link => {
            link.href = link.getAttribute('href') + cacheBuster;
        });
        const marketImg = document.querySelector('.paper img');
        if (marketImg) {
            marketImg.src = marketImg.getAttribute('src').split('?')[0] + cacheBuster;
        }

        // Smooth Hydration Popup Logic
        window.addEventListener('DOMContentLoaded', () => {
            const toastOverlay = document.getElementById('hydration-overlay');
            if (toastOverlay) {
                setTimeout(() => {
                    toastOverlay.classList.add('visible');
                }, 300);

                setTimeout(() => {
                    toastOverlay.classList.remove('visible');
                    setTimeout(() => {
                        toastOverlay.style.display = 'none';
                    }, 400); 
                }, 4300);
            }
        });

        function openModal() {
            const modal = document.getElementById('modal');
            modal.style.display = 'flex';
            setTimeout(() => modal.classList.add('active'), 10);
            
            fetch('gold_rate.json' + cacheBuster)
                .then(response => response.json())
                .then(data => {
                    const goldSticker = document.getElementById('gold-rate-display');
                    goldSticker.innerHTML = `🪙 24K Gold: ${data.rate} / gm`;
                    goldSticker.style.display = 'block';
                })
                .catch(err => console.error("Could not fetch gold rate", err));
        }

        // Old static market_stats.json fetch removed in favor of dynamic Google Sheets CSV polling.

        function closeModal(e) {
            const modal = document.getElementById('modal');
            modal.classList.remove('active');
            setTimeout(() => modal.style.display = 'none', 300);
        }
    


        const lenis = new Lenis({
            duration: 1.2,
            easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)), 
            smooth: true,
        });

        function raf(time) {
            lenis.raf(time);
            requestAnimationFrame(raf);
        }
        requestAnimationFrame(raf);

        gsap.registerPlugin(ScrollTrigger);

        // Scroll hint fade logic
        ScrollTrigger.create({
            trigger: ".gsap-track",
            start: "top 50%", 
            onEnter: () => gsap.to(".scroll-down-hint", { opacity: 0, duration: 0.3 }),
            onLeaveBack: () => gsap.to(".scroll-down-hint", { opacity: 1, duration: 0.3 })
        });

        // ==========================================
        // DYNAMIC CLIENT-SIDE TICKER (Google Sheets)
        // ==========================================
        const CSV_URL = 'https://docs.google.com/spreadsheets/d/e/2PACX-1vQ2ZyIXY5fgZSLN1rPQTIB4yw8LA99laMVJnT8eEyMAxhcBXznBsV91HmgS2RwylgYEAK-Mq4rf0JYb/pub?output=csv'; // Users will replace this with their Google Sheets published CSV link

        // Duplicate the ticker track content once so it loops seamlessly in CSS marquee
        const tickerTrack = document.getElementById('market-ticker');
        tickerTrack.innerHTML += tickerTrack.innerHTML;

        function updateTickerUI(dataRows) {
            dataRows.forEach(row => {
                const valNodes = document.querySelectorAll(`[data-ticker-val="${row.id}"]`);
                const changeNodes = document.querySelectorAll(`[data-ticker-change="${row.id}"]`);

                valNodes.forEach(node => {
                    const prefix = node.getAttribute('data-prefix') || '';
                    node.textContent = prefix + row.price;
                });

                changeNodes.forEach(node => {
                    // Clean the change string to parse as a number (handles things like ₹ or quotes)
                    const changeNum = parseFloat(row.change.replace(/[^\d.-]/g, ''));
                    const isUp = changeNum > 0;
                    const isDown = changeNum < 0;
                    
                    node.classList.remove('up', 'down');
                    if (isUp) node.classList.add('up');
                    else if (isDown) node.classList.add('down');

                    // Strip any existing plus/minus/spaces from the raw text to prevent duplicates
                    const cleanChange = row.change.replace(/[+-\s]/g, '');
                    const arrow = isUp ? '▲ +' : (isDown ? '▼ -' : '');
                    
                    node.textContent = `${arrow}${cleanChange} (${row.changePct})`;
                });
            });
        }

        function pollLiveMarketData() {
            fetch(CSV_URL)
                .then(response => {
                    if (!response.ok) throw new Error("Network response was not ok");
                    return response.text();
                })
                .then(csvText => {
                    const lines = csvText.trim().split('\n');
                    const dataRows = [];
                    for(let i = 1; i < lines.length; i++) {
                        // Regex to split by comma, ignoring commas inside double quotes
                        let cols = lines[i].split(/,(?=(?:(?:[^"]*"){2})*[^"]*$)/);
                        // Clean up quotes and whitespace from each column
                        cols = cols.map(c => c.replace(/^"|"$/g, '').trim());
                        
                        if (cols.length >= 5) {
                            dataRows.push({
                                id: cols[0],
                                price: cols[2],
                                change: cols[3],
                                changePct: cols[4]
                            });
                        }
                    }
                    updateTickerUI(dataRows);
                })
                .catch(error => {
                    console.error('Ticker update failed, retrying next cycle:', error);
                });
        }

        // Phase 2: The Polling Cycle
        pollLiveMarketData(); // Initial pull
        setInterval(pollLiveMarketData, 10 * 60 * 1000); // 10-minute loop

        // ==========================================
        // FETCH HEADLINES FOR RECEIPT
        // ==========================================
        fetch('headlines.json')
            .then(response => response.json())
            .then(data => {
                const container = document.getElementById('receipt-content');
                container.innerHTML = '';
                
                let currentPaper = '';
                
                data.forEach(item => {
                    if (item.paper !== currentPaper) {
                        currentPaper = item.paper;
                        const paperTitle = document.createElement('div');
                        paperTitle.className = 'receipt-paper-title';
                        paperTitle.textContent = currentPaper;
                        container.appendChild(paperTitle);
                    }
                    
                    const headline = document.createElement('div');
                    headline.className = 'receipt-item';
                    headline.textContent = item.title;
                    container.appendChild(headline);
                });
                
                // Set today's date
                const options = { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' };
                document.getElementById('receipt-date').textContent = new Date().toLocaleDateString('en-US', options);
                
                // Force GSAP to recalculate positions now that the receipt height has expanded!
                setTimeout(() => {
                    ScrollTrigger.refresh();
                }, 100);
            })
            .catch(error => {
                document.getElementById('receipt-content').innerHTML = '<p><i>Fresh headlines are being baked...</i></p>';
                console.error('Error fetching headlines:', error);
            });

        const tl = gsap.timeline({
            scrollTrigger: {
                trigger: ".gsap-track",
                start: "top top",
                end: "bottom bottom",
                scrub: 1.5,
                pin: ".pinned-scene"
            }
        });

        // Responsive scale targets
        const isMobile = window.innerWidth < 600;
        const finalScale = isMobile ? 1.6 : 1.5;

        // Continuous fluid zoom and rotation for the entire box
        tl.to(".master-box-container", {
            scale: finalScale,
            rotateX: 0,
            duration: 10,
            ease: "power2.inOut" 
        }, 0);

        tl.to(".scroll-down-hint", {
            opacity: 0,
            duration: 1.5
        }, 0);

        tl.to(".box-lid-img", {
            z: 150, 
            xPercent: -105, 
            yPercent: 5, 
            rotationZ: -8, 
            rotationY: 10,
            duration: 6,
            ease: "power2.inOut" 
        }, 0); 
        
        // Note: .pizza-content-wrapper no longer needs an opacity/brightness animation,
        // it simply sits under the lid and lets the realistic drop-shadow cast over it.

    