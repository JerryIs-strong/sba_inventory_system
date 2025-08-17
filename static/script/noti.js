function snapNoti(message){
    const wrapper = document.getElementById("snapNoti")

    const notiBox = document.createElement('div')
    notiBox.className("notiBox")

    const messageTxt = document.createElement('p')
    messageTxt.innerText = message

    notiBox.appendChild(message)
    wrapper.appendChil(notiBox)
}