/* Fix for Dashed Border Alignment */
function fixDashedBorder() {
    const rect = document.querySelector('.dashed-border');
    if (!rect) return;

    // 1. Get exact length of the border path
    const length = rect.getTotalLength();



    // // 2. Define desired dash/gap 
    // const desiredDash = 20;
    // const desiredGap = 15;
    // const desiredCycle = desiredDash + desiredGap;

    // 2. Load actual dash/gap
    let style = window.getComputedStyle(rect);
    const dashArray = style.strokeDasharray.replaceAll('px', '').replaceAll(" ", "").split(',').map(Number);
    const desiredDash = dashArray[0];
    const desiredGap = dashArray[1];
    const desiredCycle = desiredDash + desiredGap;
    console.log("Desired dash/gap:", desiredDash, desiredGap);

    // 3. Calculate how many full cycles fit into the length
    const count = Math.round(length / desiredCycle);

    // 4. Adjust the cycle length to fit exactly
    const realCycle = length / count;

    // 5. recalculate dash and gap to maintain ratio
    const ratio = desiredDash / desiredCycle;
    const realDash = realCycle * ratio;
    const realGap = realCycle * (1 - ratio);

    // 6. Apply new values
    rect.style.strokeDasharray = `${realDash} ${realGap}`;
    rect.style.setProperty('--dash-offset', `-${realCycle}`);
}

window.addEventListener('load', fixDashedBorder);
window.addEventListener('resize', fixDashedBorder);
// Also run immediately in case DOM is ready
fixDashedBorder();


// console.log("Starting dashed border animation loop...");
// let abcd = true;
// setInterval(()=>{
//     if( abcd ){
//         abcd = false;
//         document.querySelector('.drag-area').classList.remove('finish');
//         document.querySelector('.drag-area').classList.add('active');

//     } else {
//         abcd = true;
//         document.querySelector('.drag-area').classList.remove('active');
//         document.querySelector('.drag-area').classList.add('finish');

//     }   

// }, 2000);