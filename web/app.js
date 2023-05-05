function setEyeDirection(x, y) {
    const leftEye = document.getElementById('left-eye');
    const rightEye = document.getElementById('right-eye');
    const eyes = [leftEye, rightEye];

    eyes.forEach((eye) => {
        eye.style.transform = `translate(-50%, -50%) translate(${x}px, ${y}px)`;
    });
}
