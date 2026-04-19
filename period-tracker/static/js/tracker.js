let startDate = null, endDate = null;
let currentYear = new Date().getFullYear();

document.addEventListener('DOMContentLoaded', () => {
    renderTopScroller();
    updateWaterDisplay();
});

let waterAmount = 0;

function updateWaterDisplay() {
    const counter = document.getElementById('waterAmount');
    if (counter) counter.innerText = waterAmount;
}

function changeWater(delta) {
    waterAmount = Math.max(0, waterAmount + delta);
    updateWaterDisplay();
}

function openDrawer() {
    document.getElementById('drawerOverlay').classList.remove('hidden');
    renderYear();
}

function closeDrawer() { 
    document.getElementById('drawerOverlay').classList.add('hidden'); 
    startDate = null; endDate = null;
}

function changeYear(step) {
    currentYear += step;
    renderYear();
}

function renderYear() {
    const container = document.getElementById('yearContainer');
    document.getElementById('displayYear').innerText = currentYear;
    container.innerHTML = '';

    for (let m = 0; m < 12; m++) {
        const section = document.createElement('div');
        section.className = 'month-section';
        const name = new Date(currentYear, m).toLocaleString('default', { month: 'long' });
        section.innerHTML = `<div class="month-name">${name}</div><div class="calendar-grid" id="grid-${m}"></div>`;
        container.appendChild(section);
        renderMonthGrid(m, document.getElementById(`grid-${m}`));
    }
}

function renderMonthGrid(month, grid) {
    const days = new Date(currentYear, month + 1, 0).getDate();
    const first = new Date(currentYear, month, 1).getDay();
    let offset = first === 0 ? 6 : first - 1;
    const today = new Date();
    today.setHours(0, 0, 0, 0); // Reset time for date comparison

    for (let x = 0; x < offset; x++) grid.appendChild(document.createElement('div'));

    for (let i = 1; i <= days; i++) {
        const day = document.createElement('div');
        const dateObj = new Date(currentYear, month, i);
        day.className = 'cal-day';
        day.innerText = i;
        
        if (startDate && dateObj.getTime() === startDate.getTime()) day.classList.add(endDate ? 'selected-start' : 'single-day');
        if (endDate && dateObj.getTime() === endDate.getTime()) day.classList.add('selected-end');
        if (startDate && endDate && dateObj > startDate && dateObj < endDate) day.classList.add('in-range');

        // Disable clicking on future dates
        if (dateObj > today) {
            day.style.opacity = '0.5';
            day.style.cursor = 'not-allowed';
        } else {
            day.onclick = () => {
                if (!startDate || (startDate && endDate)) { startDate = dateObj; endDate = null; }
                else if (dateObj < startDate) { startDate = dateObj; }
                else { endDate = dateObj; }
                renderYear();
                document.getElementById('confirmBtn').disabled = !endDate;
            };
        }
        grid.appendChild(day);
    }
}

function renderTopScroller() {
    const scroller = document.getElementById('topScroller');
    if (!scroller) return;
    scroller.innerHTML = ''; 
    
    const today = new Date();
    const startOfWeek = new Date(today);
    const dayDiff = today.getDay() === 0 ? 6 : today.getDay() - 1;
    startOfWeek.setDate(today.getDate() - dayDiff);

    for (let i = 0; i < 7; i++) {
        const d = new Date(startOfWeek);
        d.setDate(startOfWeek.getDate() + i);
        const isToday = d.toDateString() === today.toDateString();
        const item = document.createElement('div');
        item.className = `date-item ${isToday ? 'active' : ''}`;
        item.innerHTML = `
            <span>${d.toLocaleString('default', {weekday: 'short'})}</span>
            <strong>${d.getDate()}</strong>
            ${isToday ? '<div class="dot"></div>' : ''}
        `;
        scroller.appendChild(item);
    }
}

function savePeriod() {
    fetch('/log_period', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            start: startDate.toISOString().split('T')[0],
            end: endDate.toISOString().split('T')[0]
        })
    }).then(res => res.ok && window.location.reload());
}