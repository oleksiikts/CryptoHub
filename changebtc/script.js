// Проста функція для симуляції конвертації
function calculate() {
    const amount = parseFloat(document.getElementById('amount').value);
    const crypto = document.getElementById('crypto').value;
    const currency = document.getElementById('currency').value;

    // Симуляція курсів конвертації
    const rates = {
        bitcoin: { usd: 30000, eur: 28000 },
        ethereum: { usd: 2000, eur: 1800 }
    };

    if (rates[crypto] && rates[crypto][currency]) {
        const rate = rates[crypto][currency];
        const result = amount * rate;
        document.getElementById('result').innerText = 
            `${amount} ${crypto.toUpperCase()} is approximately ${result.toFixed(2)} ${currency.toUpperCase()}`;
    } else {
        document.getElementById('result').innerText = 'Conversion rate not available';
    }
}
