function get_socket() {
    const socket = io();
        
socket.on('get_update',function (data) {
    da = JSON.stringify(data)
    d = JSON.parse(da)
    for(let update in d){
      get_element = document.getElementById(update).textContent
      alert(get_element)    
    }
})
}