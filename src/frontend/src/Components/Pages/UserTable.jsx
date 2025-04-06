import {
    EditableProTable
} from '@ant-design/pro-components';
import React, {useEffect, useState} from 'react';
import ruRU from 'antd/es/locale/ru_RU';
import {Button, ConfigProvider} from 'antd';
import dayjs from 'dayjs';
import 'dayjs/locale/ru';
import {DeleteFilled, EditFilled} from "@ant-design/icons";
import {createUser, deleteUser, fetchAllUser, updateUser} from "../../services/Networking/User.jsx";

dayjs.locale('ru');


export default function UserTable() {
    const [editableKeys, setEditableKeys] = useState([]);
    const [dataSource, setDataSource] = useState([]);

    useEffect(() => {
        fetchAllUser()
            .then(data => {
                setDataSource(data);
            })
            .catch(console.error)
    }, [])

    const columns = [
        {
            title: "ID",
            dataIndex: "tg_id",
            formItemProps: {
                initialValue: "",
                rules: [
                    {
                        required: true,
                        message: "Укажите id"
                    }
                ]
            }
        },
        {
            title: "ФИО",
            dataIndex: "fio",
            formItemProps: {
                initialValue: "",
                rules: [
                    {
                        required: true,
                        message: "Укажите ФИО"
                    }
                ]
            }
        },
        {
            title: "Группа",
            dataIndex: "group",
            formItemProps: {
                rules: [
                    {
                        required: true,
                        message: "Укажите группу"
                    }
                ]
            }
        },
        {
            title: "Дата рождения",
            dataIndex: "birthday",
            valueType: "date",
            formItemProps: {
                rules: [
                    {
                        required: true,
                        message: "Укажите дату рождения"
                    }
                ]
            }
        },
        {
            title: "Статус",
            dataIndex: "status",
            valueType: "select",
            valueEnum: {
                active: {
                    text: "Работает",
                    status: "Success"
                },
                deactive: {
                    text: "Уволен",
                    status: "Error"
                },
                check: {
                    text: "На проверке",
                    status: "Warning"
                }
            },
            formItemProps: {
                initialValue: "check"
            }
        },
        {
            title: "Админ",
            dataIndex: "is_admin",
            valueEnum: {
                true: {
                    text: "Да",
                    status: "Success"
                },
                false: {
                    text: "Нет",
                    status: "Default"
                }
            },
            formItemProps: {
                rules: [
                    {
                        required: true,
                    }
                ],
                initialValue: "false"
            }
        }, {
            title: 'Логин', dataIndex: 'user_login',
        }, {
            title: 'Операции',
            valueType: 'option',
            render: (text, record, _, action) => [<a key="edit" onClick={() => action?.startEditable?.(record.tg_id)}>
                <Button color={'orange'} variant={"outlined"}>
                    <EditFilled/>
                </Button>
            </a>, <a key="delete" onClick={async () => {
                try {
                    await deleteUser(record.tg_id);
                    // Локально убираем эту запись из массива
                    setDataSource((prev) => prev.filter((item) => item.tg_id !== record.tg_id));
                } catch (err) {
                    console.error(err);
                }
            }}>
                <Button color={'red'} variant={"outlined"}>
                    <DeleteFilled/>
                </Button>
            </a>,],
        },];
    return (<>
        <ConfigProvider locale={ruRU}>
            <EditableProTable
                rowKey="tg_id"
                headerTitle="Пользователи"
                columns={columns}
                value={dataSource}
                onChange={setDataSource}
                editable={{
                    type: 'multiple',
                    editableKeys,
                    onSave: async (rowKey, record /* , originRow */) => {
                        try {
                            if (record.isNew) {
                                // Если запись помечена как новая — создаём пользователя (POST)
                                const {data: created} = await createUser(record);

                                // Предположим, что бэкенд вернул JSON вида { "tg_id": <число>, ... }
                                // Тогда локально обновляем dataSource, заменив временную запись на реальную
                                setDataSource((prev) =>
                                    prev.map((item) => (item.tg_id === rowKey ? created : item))
                                );
                            } else {
                                // Иначе изменяем существующего пользователя (PATCH)
                                const {data: updated} = await updateUser(rowKey, record);

                                // Заменяем старую запись на обновлённую
                                setDataSource((prev) =>
                                    prev.map((item) => (item.tg_id === rowKey ? updated : item))
                                );
                            }
                        } catch (error) {
                            console.error('Ошибка при сохранении:', error);
                        }
                    }, onChange: setEditableKeys,
                }}

                recordCreatorProps={{
                    record: () => ({
                        tg_id: 1,
                        isNew: true
                    }), creatorButtonText: 'Добавить пользователя',
                }}
            />
        </ConfigProvider>
    </>);
}