const menuToggle = document.querySelector('.menu-btn')

const showMenuBar = () => {
    const burger = document.querySelector('.burger');
    const mainMenu = document.querySelector('#phone-menu');
    if (mainMenu.classList.contains('closed')) {
        mainMenu.classList.toggle('closed');
        burger.classList.toggle('active');
    } else {
        mainMenu.classList.toggle('closed');
        burger.classList.toggle('active');
    };
};
menuToggle.addEventListener('click', showMenuBar)