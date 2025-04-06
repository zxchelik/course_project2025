import Api from "./api.jsx";

export async function fetchUserById(userId) {
    const res = await Api.get(`/users/${userId}`);
    return res.data;
}

export async function fetchAllUser() {
    const res = await Api.get(`/users/`);
    return res.data;
}
export async function deleteUser(userId) {
    await Api.delete(`/users/${userId}`)
}

/**
 * Создаёт нового пользователя, отправляя POST на /users.
 * Возвращает промис (результат axios-запроса).
 * @param {Object} userData - данные пользователя
 * @param {string} userData.fio
 * @param {string} [userData.group]
 * @param {string} userData.birthday  // в формате 'YYYY-MM-DD'
 * @param {string} [userData.status]  // по умолчанию "check"
 * @param {boolean} [userData.is_admin]
 * @param {string} [userData.user_login]
 * @param {string} [userData.hashed_password]
 * @returns {Promise} - Промис с ответом от сервера
 */
export function createUser(userData) {
    console.log(userData);
    return Api.post('/users', userData);
}

/**
 * Частично обновляет пользователя (PATCH /users/:tg_id).
 * Поля, не переданные в userData, не изменятся.
 * @param {number} tgId - tg_id пользователя, которого нужно изменить
 * @param {Object} userData - данные для обновления
 * @returns {Promise} - Промис с ответом от сервера
 */
export function updateUser(tgId, userData) {
    return Api.patch(`/users/${tgId}`, userData);
}