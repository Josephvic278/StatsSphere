function get_socket() {
    const socket = io();
        
socket.on('get_update',function (data) {
    d = JSON.stringify(data)
    data = JSON.parse(d)
    for (update_date in d) {
        alert(update_date)
    }
})
}