export function formatPhoneNumber(phoneNumber) {
    const cleanedNumber = phoneNumber.replace(/\D/g, '');

    if (cleanedNumber.length === 11 && cleanedNumber.startsWith('1')) {
        const countryCode = cleanedNumber.slice(0, 1);
        const areaCode = cleanedNumber.slice(1, 4);
        const centralOfficeCode = cleanedNumber.slice(4, 7);
        const lineNumber = cleanedNumber.slice(7, 11);
        const num = `+${countryCode} (${areaCode}) ${centralOfficeCode}-${lineNumber}`
        return num;
    } else {
        throw new Error("Invalid phone number format");
    }
}


export function convertTo12Hour(time24) {
    let [hours, minutes] = time24.split(':').map(Number);
    let period = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12 || 12;
    let formattedHours = hours.toString().padStart(2, '0');
    let formattedMinutes = minutes.toString().padStart(2, '0');
    return `${formattedHours}:${formattedMinutes} ${period}`;
}