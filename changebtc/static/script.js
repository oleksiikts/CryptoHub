document.getElementById('crypto-converter').addEventListener('submit', function(e) {
    e.preventDefault();

    let cryptoSelect = document.getElementById('cryptoSelect').value;
    let cryptoAmount = document.getElementById('cryptoAmount').value;
    let usdAmountField = document.getElementById('usdAmount');

    let rates = {
        'btc': 40000,   // курс для BTC
        'sol': 20,      // курс для SOL
        'eth': 3000     // курс для ETH
    };

    let usdAmount = cryptoAmount * rates[cryptoSelect];
    usdAmountField.value = usdAmount.toFixed(2);
});
