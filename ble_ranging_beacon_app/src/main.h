/*
 * Copyright (c) 2022, Silvano Cortesi
 * Copyright (c) 2022, ETH Zürich
 *
 * SPDX-License-Identifier: Apache-2.0
 */
#ifndef _MAIN_H
#define _MAIN_H

#include <zephyr/kernel.h>

int charging_int_init(struct k_msgq *charging_state_queue_param);

#endif //_MAIN_H
