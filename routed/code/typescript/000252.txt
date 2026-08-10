import React, {FormEvent, useEffect, useState} from 'react';
import {Link} from 'react-router-dom';
import {Breadcrumb, Card, Col} from 'react-bootstrap';
import {StateInterface} from '../../store/store';
import {useDispatch, useSelector} from 'react-redux';
import {clearError, setError} from "../utils/Error";
import {getUser, patchUser} from "../../api/user/userApi";
import {Form} from "react-bootstrap";
import UserModel from "../../model/UserModel";
import {History, Location} from "history";
import FormInputModal, {ElementType} from "../utils/FormInputModal";
import LoadingButton from "../utils/LoadingButton";

type ProfileFormProps = {
    history: History;
    location: Location<{profileId: string}>;
}
const Profile: React.FC<ProfileFormProps> = ({history, location}) => {
    const lang = useSelector((state: StateInterface) => state.lang);
    const [validated, setValidated] = useState(false);
    const dispatch = useDispatch();
    const [profile, setProfile] = useState(new UserModel());
    const [isDisplayFormInput, setIsDisplayFormInput] = useState(false);

    useEffect(() => {
        (async () => {
            const response = await getUser(location.state.profileId);
            setProfile(response.data)
        })();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
        setValidated(true);
        clearError(dispatch);
        event.preventDefault();

        if (!event.currentTarget.checkValidity()) {
            setError(dispatch, lang['error-form-required']);
            return;
        }

        setIsDisplayFormInput(true);
    };

    const updateProfileHandler = (item: any) => {
        setIsDisplayFormInput(false);
        if (!profile.password || profile.password === '') {
            setError(dispatch, lang['password-required']);
            return;
        }
        (async () => {
            try {
                await patchUser(profile);
                window.location.reload();
            } catch (err) {
                setError(dispatch, err.message);
            }
        })();
    };

    const handleChange = (element: any) => {
        clearError(dispatch);
        setProfile({...profile, [element.target.name]: element.target.value});
    };

    const onPasswordChange = (value: string) => {
        setProfile({...profile, password: value});
    };

    return (
        <>
            <Breadcrumb>
                <Breadcrumb.Item active>
                    <Link to={'/'}>Dashboard</Link>
                </Breadcrumb.Item>
                <Breadcrumb.Item active>
                    <Link to={'/user'}>{lang['user']}</Link>
                </Breadcrumb.Item>
                <Breadcrumb.Item active>
                    {lang['profile']}
                </Breadcrumb.Item>
            </Breadcrumb>
            <h2>{lang['profile']}</h2>
            <Card>
                <Card.Body>
                    <Form noValidate validated={validated} onSubmit={handleSubmit} onChange={(e: FormEvent<HTMLFormElement>) => {handleChange(e)}}>
                        <Form.Row>
                            <Form.Group as={Col}>
                                <Form.Label>{lang['first-name']}</Form.Label>
                                <Form.Control autoComplete={'off'} required name={'firstName'} defaultValue={profile.firstName} />
                            </Form.Group>
                            <Form.Group as={Col}>
                                <Form.Label>{lang['last-name']}</Form.Label>
                                <Form.Control autoComplete={'off'} required name={'lastName'} defaultValue={profile.lastName} />
                            </Form.Group>
                        </Form.Row>
                        <Form.Group>
                            <Form.Label>Email</Form.Label>
                            <Form.Control autoComplete={'off'} readOnly type={'email'} name={'email'} defaultValue={profile.email} />
                        </Form.Group>
                        <Form.Group>
                            <Form.Label>{lang['phone-number']}</Form.Label>
                            <Form.Control autoComplete={'off'} required name={'phone'} defaultValue={profile.phone} />
                        </Form.Group>
                        <LoadingButton loading={false}>{lang['save']}</LoadingButton>
                    </Form>
                </Card.Body>
            </Card>
            <FormInputModal item={profile} title={lang['password-confirm']} elements={[{
                value: profile.password || '', required: true, type: ElementType.PASSWORD, name: 'form-input-password', onChange: onPasswordChange
            }]} isDisplay={isDisplayFormInput} onCancelAction={(item: any) => setIsDisplayFormInput(false)} onOkAction={updateProfileHandler} />
        </>
    );
};

export default Profile;